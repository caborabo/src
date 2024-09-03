import yaml
import datetime
import re
from english_dictionary.scripts.read_pickle import get_dict
from datetime import timedelta

from .shared import (
    read_talk_csv,
    generate_short_url,
    pick_picture_file,
    start_time,
)
from .assemblyai import (
    read_transcript,
)
from .srt import (
    read_srt_transcript,
)
english_dict = get_dict()


def get_metadata():
    context = dict()
    with open('metadata.yml') as f:
        context = yaml.load(f, Loader=yaml.FullLoader)
    return context

def get_enriched_metadata(base_folder):
    context = get_metadata()

    # sort the events
    events = context.get("events")
    events.sort(key=lambda e: e.get("date"))

    # extract a bunch of things for easier templating out later
    future_events = []
    past_events = []
    years = dict()
    featured_sponsors = set()
    for event in events:
        # sort sponsors
        for sponsor_type in event.get("sponsors", {}).keys():
            event["sponsors"][sponsor_type].sort()
            if sponsor_type in ["platinum", "diamond"]:
                for sponsor in event["sponsors"][sponsor_type]:
                    featured_sponsors.add(sponsor)
        # divide into past and future events
        if datetime.date.today() + datetime.timedelta(days=2) >= event.get("date"):
            event["cfp_closed"] = True
            past_events.append(event)
        else:
            future_events.append(event)
        # bucket by year
        year = str(event.get("date").year)
        event["year"] = year
        if year not in years:
            years[year] = []
        years[year].append(event)
        # mark as revealed or not
        event["reveal_videos"] = False
        vrd = event.get("videos_reveal_date")
        if vrd is not None and datetime.date.today() >= vrd:
            event["reveal_videos"] = True
    context["years"] = years
    context["years_sorted"] = sorted(years.keys(), reverse=True)
    context["future_events"] = future_events
    context["current_event"] = past_events[-1]
    context["past_events"] = past_events[:-1]
    context["past_events"].sort(key=lambda e: e.get("date"), reverse=True)
    context["featured_sponsors"] = sorted(list(featured_sponsors))

    # match up with prior years
    for event in events:
        url = event.get("short_url")
        others = []
        event["other_editions"] = others
        if not url:
            continue
        for year in context.get("years").keys():
            if event.get("year") == year:
                continue
            for candidate in context.get("years").get(year):
                # discard the last 4 chars - the year
                url_candidate = candidate.get("short_url")
                if not url_candidate:
                    continue
                if url_candidate[:-4] == url[:-4]:
                    others.append({
                        "year": year,
                        "short_url": url_candidate,
                    })
        others.sort(key=lambda x: x.get("year"))

    # read in the talks database
    for event in events:
        # for external URLs, just use that as url
        if "external_url" in event:
            event["url"] = event["external_url"]
            continue
        else:
            event["url"] = context.get("base_path") + event["short_url"]

        # attempt to read the talks CSV
        try:
            talks = read_talk_csv(event.get("db_path"))
        except:
            talks = []
        event["talks_raw"] = talks

        # check and pick the picture
        event["thumbnail_path"] = pick_picture_file(base_folder + "/", event["thumbnail_path"])

        # split into featured and not
        event["talks_featured"] = [talk for talk in talks if talk.get("Featured","").lower() == "yes"]
        event["talks_panel"] = [talk for talk in talks if talk.get("Panel","").lower() == "yes"]
        context["panels"] = context.get("panels", []) + event["talks_panel"]
        event["talks"] = [
            talk for talk in talks
            if talk.get("Featured","").lower() != "yes" and talk.get("Panel","").lower() != "yes"
        ]

        #counts
        print("%s %s /%s (%d talks, %d keynotes, %d panels)" % (event.get("date"), event.get("name"), event.get("short_url"), len(event["talks"]), len(event["talks_featured"]), len(event["talks_panel"])))

        # extract and store the tracks
        tracks_ordered = []
        tracks = dict()
        for talk in event["talks"]:
            track = talk.get("Track", "other")
            if track not in tracks:
                tracks[track] = []
            tracks[track].append(talk)
            tracks_ordered.append(track)
        event["tracks"] = tracks
        event["tracks_ordered"] = tracks_ordered

        # offset other tracks with that duration
        DEFAULT_DURATION = 30
        start = start_time(event.get("date"))
        end = start_time(event.get("date"))
        for i, track in enumerate(tracks_ordered):
            current_time = start_time(event.get("date"))
            current_time += timedelta(minutes=event.get("premiere_duration", 0))
            for talk in event["talks_featured"] + event["talks_panel"]:
                talk["start_time"] = current_time
                talk["duration"] = int(talk.get("duration") or DEFAULT_DURATION)
                talk["offset"] = (current_time - start).total_seconds()/60
                current_time += timedelta(minutes=talk["duration"])
            for talk in tracks[track]:
                talk["start_time"] = current_time
                talk["duration"] = int(talk.get("duration") or DEFAULT_DURATION)
                talk["offset"] = (current_time - start).total_seconds()/60
                current_time += timedelta(minutes=talk["duration"])
            if current_time > end:
                end = current_time

        context["talks_by_tracks"] = tracks
        event["talks_start"] = start
        event["talks_end"] = end
        event["talks_end_offset"] = (end - start).total_seconds()/60
        event["hallway_start"] = start - timedelta(hours=1)
        event["hallway_end"] = start
        #print("Loaded %d confirmed talks in %d tracks: %s" % (len(event["talks"]), len(tracks), tracks.keys()))

        # enrich the talks
        for talk in talks:
            talk["short_url"] = generate_short_url(event, talk)
            talk["YouTubeId"] = talk.get("YouTube", "").split("/")[-1]

            # check if transcript exists
            transcript = read_transcript(talk["YouTubeId"])
            if transcript:
                talk["transcript"] = transcript
                continue
            transcript = read_srt_transcript(talk["Name1"], event["short_url"])
            if transcript:
                talk["transcript"] = transcript
            
    return context

def extract_keywords(talk):
    keywords = ["Conf fourty two"]
    # append some fields as they are - e.g. Amazon Web Services, or Site Reliability Engineer
    for field in ["JobTitle1", "JobTitle2", "Name1", "Name2", "Company1", "Company2"]:
        content = talk.get(field)
        keywords.append(content)
    # append all words from the list
    for field in ["Title", "Abstract"]:
        content = talk.get(field)
        # replace whitespace with _
        content = re.sub('[\s]+', '_', content)
        # remove all non-word characters
        content = re.sub('[\W]+', '', content)
        # add back the keywords separated by _
        keywords.extend(content.split("_"))
    # append comma-separated keywords
    for field in ["Keywords"]:
        content = talk.get(field)
        keywords.extend(content.split(","))
    # lowercase
    keywords = [word.lower() for word in keywords]
    # remove common words and non-letters
    keywords = [
        re.sub('[^a-z ]', '', word)
        for word in keywords
        if word not in english_dict
    ]
    # remove empties
    keywords = [word for word in keywords if word]
    # cut out the words if any longer than 6
    keywords = [
        " ".join(word.split(" ")[:6])
        for word in keywords
    ]
    # deduplicate and only first 1000
    return sorted(list(set(keywords))[:1000])
