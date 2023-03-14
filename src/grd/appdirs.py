import appdirs

dirs = appdirs.AppDirs("github-release-downloader", "thegamecracks")


if __name__ == "__main__":
    print(f"{dirs.site_config_dir = !s}")
    print(f"{dirs.site_data_dir = !s}")
    print(f"{dirs.user_cache_dir = !s}")
    print(f"{dirs.user_config_dir = !s}")
    print(f"{dirs.user_data_dir = !s}")
    print(f"{dirs.user_log_dir = !s}")
    print(f"{dirs.user_state_dir = !s}")
