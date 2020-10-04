# coding: utf-8

from django.db import models


class CrawlerTarget(models.Model):
    id = models.IntegerField(primary_key=True)
    status = models.IntegerField(default=0)
    creation = models.DateTimeField(auto_now=True)
    fw_id = models.IntegerField(default=-1)
    fw_hash = models.CharField(max_length=250, default="")
    url = models.CharField(max_length=250)
    vendor = models.CharField(max_length=250)
    device_name = models.CharField(max_length=250)

    class Meta:
        managed = False
        db_table = 'corsica_crawler_targets'


class TestDevice(models.Model):
    id = models.IntegerField(primary_key=True)
    fw_id = models.IntegerField()
    scheme = models.CharField(max_length=250, default="http://")
    address = models.CharField(max_length=250)
    port = models.IntegerField(default=80)

    class Meta:
        managed = False
        db_table = 'corsica_test_devices'


class JobQueue(models.Model):
    id = models.IntegerField(primary_key=True)
    service = models.CharField(max_length=250, default="")
    action = models.CharField(max_length=250, default="")
    creation = models.DateTimeField(auto_now=True)
    status = models.IntegerField(default=0)
    in_data = models.TextField(default="{}")
    out_data = models.TextField(default="{}")
    log = models.CharField(max_length=250, default="")

    class Meta:
        managed = False
        db_table = 'job_queue'


class FirmwareMeta(models.Model):
    id = models.IntegerField(primary_key=True)
    created = models.DateTimeField(auto_now=True)
    filename = models.CharField(max_length=250)
    vendor = models.CharField(max_length=250)
    version = models.CharField(max_length=250)
    devicename = models.CharField(max_length=250)
    size = models.IntegerField()
    hash_sum = models.CharField(max_length=250)
    processed = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'firmware_meta'


class TSRemoteResult(models.Model):
    id = models.IntegerField(primary_key=True)
    fw_id = models.IntegerField()
    browser = models.CharField(max_length=250)
    date = models.DateTimeField(auto_now=True)
    result = models.TextField()

    class Meta:
        managed = False
        db_table = 'ts_remote_results'


class ShodanQuery(models.Model):
    id = models.IntegerField(primary_key=True)
    status = models.IntegerField(default=0)
    query = models.CharField(max_length=250, default="")

    class Meta:
        managed = False
        db_table = 'shodan_queries'


class ShodanDevice(models.Model):
    id = models.IntegerField(primary_key=True)
    query_id = models.IntegerField(default=0)
    address = models.CharField(max_length=250, default="")
    port = models.IntegerField(default=0)
    information = models.TextField()

    class Meta:
        managed = False
        db_table = 'shodan_devices'


class JavaScriptValue(models.Model):
    id = models.IntegerField(primary_key=True)
    created = models.DateTimeField(auto_now=True)
    group_id = models.CharField(max_length=250, default="")
    name = models.CharField(max_length=250, default="")
    value = models.TextField()

    class Meta:
        managed = False
        db_table = 'javascript_values'


class WebRootFiles(models.Model):
    id = models.IntegerField(primary_key=True)
    firmware = models.IntegerField(default=0)
    file_id = models.IntegerField(default=0)
    hash = models.CharField(max_length=255, default="")
    web_root = models.IntegerField(default=0)
    filename = models.CharField(max_length=255, default="")
    local_path = models.CharField(max_length=512, default="")
    web_path = models.CharField(max_length=255, default="")
    web_full_path = models.CharField(max_length=255, default="")
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'corsica_web_root_files'


class FingerprinterElement(models.Model):
    id = models.IntegerField(primary_key=True)
    status = models.IntegerField(default=0)
    creation = models.DateTimeField(auto_now=True)
    browser = models.CharField(max_length=255, default="")
    url = models.CharField(max_length=255, default="")
    result = models.TextField()

    class Meta:
        managed = False
        db_table = 'corsica_fingerprinter'


class WebRoots(models.Model):
    id = models.IntegerField(primary_key=True)
    firmware = models.ForeignKey(FirmwareMeta, on_delete=models.CASCADE, db_column='firmware')
    hash_web_root = models.CharField(max_length=255, default="")
    path_web_root = models.CharField(max_length=255, default="")
    path_web_root_real = models.CharField(max_length=255, default="")

    class Meta:
        managed = False
        db_table = 'corsica_web_roots'
