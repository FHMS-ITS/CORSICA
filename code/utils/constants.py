DB_MEM = {"FP_FILE_FINGERPRINT": "mem_fp_file_fingerprint",
          "FP_WEB_ROOT_FILES": "mem_fp_webroot_files",
          "FP_WEB_ROOTS": "mem_fp_webroots",
          "FP_WEB_PATH_COUNT": "mem_fp_webpath_count",
          "FP_PARTS": "mem_fp_parts",
          "FP_FILE_FINGERPRINT_ERROR": "mem_fp_file_fingerprint_error"}

DB_PERS = {"FP_FILE_FINGERPRINT": "fp_file_fingerprint",
           "FP_WEB_ROOT_FILES": "fp_webroot_files",
           "FP_WEB_ROOTS": "fp_webroots",
           "FP_WEB_PATH_COUNT": "fp_webpath_count",
           "FP_PARTS": "fp_parts",
           "FP_FILE_FINGERPRINT_ERROR": "fp_file_fingerprint_error"}

DB_WORK = DB_MEM

CRAWL_STAT_ERR_EMPTY_RES = -2
CRAWL_STAT_ERR_TIMEOUT = -1
CRAWL_STAT_NOT_PROCESSED = 0

CRAWL_STAT_IN_PROGRESS = 1
CRAWL_STAT_CRAWL_SUCCESS = 2
CRAWL_STAT_FIRM_CREATED = 3
CRAWL_STAT_FIRM_SCANNED = 4
CRAWL_STAT_FINISHED = 5

LANG = {
    "CRAWLER": {
        "STATUS":
            {
                CRAWL_STAT_ERR_EMPTY_RES: "Result was empty",
                CRAWL_STAT_ERR_TIMEOUT: "Timeout error",
                CRAWL_STAT_NOT_PROCESSED: "Not processed Yet",
                CRAWL_STAT_IN_PROGRESS: "In progress",
                CRAWL_STAT_CRAWL_SUCCESS: "Crawling successful",
                CRAWL_STAT_FIRM_CREATED: "Firmware created",
                CRAWL_STAT_FIRM_SCANNED: "Firmware scanned",
                CRAWL_STAT_FINISHED: "Finished",
            }
    }

}

JOB_STATUS_WARNING = -2
JOB_STATUS_ERROR = -1
JOB_STATUS_CREATED = 1
JOB_STATUS_STARTED = 2
JOB_STATUS_SUCCESS = 5
