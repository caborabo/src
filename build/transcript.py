def parse_time_start(time_start):
    """
        Turns something like
        00:00:37,644 --> 00:00:41,286
        into seconds
    """
    seconds = 0
    multiplier = 3600 # hours
    for elem in time_start.split(",")[0].split(":"):
        seconds += multiplier * int(elem)
        multiplier /= 60
    return seconds

def parse_srt(transcript):
    chunks = []
    for elem in transcript.split("\n\n"):
        # handle extra whitespace
        if not elem.strip():
            continue
        try:
            split_elemts = elem.split("\n")
            time_line = split_elemts[1]
            text = split_elemts[2:]
        except Exception as ex:
            print(f"Unexpected format ({ex}): {elem}")
        time_start = time_line.split(" ")[0]
        seconds = parse_time_start(time_start)
        chunks.append(dict(
            text=text,
            timestamp=time_start,
            timestamp_s=seconds,
        ))
    return chunks
