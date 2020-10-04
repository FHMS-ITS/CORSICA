from apps.generator.fingerprint.generators.version_fingerprint_generator import VersionFingerprintGenerator
from apps.generator.manager.MgrFingerprintCreation import MgrFingerprintCreation
from apps.generator.manager.MgrWebRootExtraction import MgrWebRootExtraction


# ToDo: Write data persisting for SQLAlchemy
from utils.log import _info


def persist_data(engine):
    #    for db in DB_MEM:
    #        self.query("INSERT " + DB_PERS[db] + " SELECT * FROM " + DB_MEM[db] + ";")
    pass


def run_extraction(config, db_engine, args):
    mgr_web_root_extraction = MgrWebRootExtraction(config, db_engine, args)
    mgr_web_root_extraction.work()


# ToDo: Refactoring
def run_generation(config, db_engine, args):
    mgr_fingerprint_creation = MgrFingerprintCreation(config, db_engine, args)
    mgr_fingerprint_creation.work()
    pass

def run_version_generator(config, db_engine, args):
    mgr_version_fingerprint_creation = VersionFingerprintGenerator(config, db_engine, args)
    mgr_version_fingerprint_creation.run()

def copy_dbs(db_engine, src, dst):
    _info("corsica.fpgen.dae", "Copy Database from {src} to {dst}".format(src=src, dst=dst))
    dbs = ['fp_file_fingerprint',
           'fp_file_fingerprint_error',
           'fp_parts',
           'web_path_count',
           'web_roots',
           'web_root_files',
           ]

    for db in dbs:
        db_engine.execute("TRUNCATE TABLE {dst}_{db};".format(db=db, src=src, dst=dst))
        db_engine.execute("INSERT {dst}_{db} SELECT * FROM {src}_{db};".format(db=db, src=src, dst=dst))


def run_all(config, db_engine, args):
    run_extraction(config, db_engine, args)
    run_generation(config, db_engine, args)


def run(config, db_engine, args):
    actions = {"all": run_all, "extract": run_extraction, "generate": run_generation, "version_generator": run_version_generator}

    if args.action in actions:
        copy_dbs(db_engine, 'corsica', 'mem')
        actions[args.action](config, db_engine, args)
        copy_dbs(db_engine, 'mem', 'corsica')
    else:
        print("No action defined")
