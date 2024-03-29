from voluptuous import Schema, Required, All, In, Length, Range, Optional, Match, Coerce

match = r"^[a-z_A-Z_0-9_\-\.]*([,，]*[a-z_A-Z_0-9_\-\.])*$"

update_setting = Schema({
    Required("website"): {
        Required("version"): All(str, Length(max=10)),
        Required("title"): All(str, Length(min=1, max=20)),
        Required("name"): All(str, Length(min=1, max=20)),
        Required("notice"): All(str, Length(max=200)),
        Optional("icon"): All(str, Length(max=200))
    },
    Required("preview"): {
        Required("office"): All(str, Match(match)),
        Required("text"): All(str, Match(match)),
        Required("image"): All(str, Match(match)),
        Required("audio"): All(str, Match(match)),
        Required("video"): All(str, Match(match)),
        Required("auto_play_audio"): bool,
        Required("auto_play_video"): bool,
        Required("thumbnail"): bool,
    },
    Required("fs"): {
        Required("pagination_mode"): All(Coerce(int), In([1, 2, 3])),
        Required("pagination_size"): All(Coerce(int), Range(min=10, max=100)),
        Required("max_upload_size"): All(Coerce(int), Range(max=1024 * 1024 * 1024 * 30)),
        Required("max_download_size"): All(Coerce(int), Range(max=1024 * 1024 * 1024 * 30)),
        Required("max_parallel"): All(Coerce(int), Range(min=1, max=10)),
        Required("chunk_size"): All(Coerce(int), Range(max=1024 * 1024 * 100)),
        Required("skip_files"): All(str, Match(match))
    }
})
