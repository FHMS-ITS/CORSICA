from apps.fingerprinter.actions import run_fingerprinter, run_plugins
from apps.generator.fingerprint.generators.version_fingerprint_generator import VersionFingerprintGenerator
from apps.generator.manager.MgrFingerprintCreation import MgrFingerprintCreation
from apps.generator.manager.MgrWebRootExtraction import MgrWebRootExtraction


from utils.log import _info

def run(config, db_engine, args):
    actions = {"run": run_fingerprinter, "calculate_plugins": run_plugins}

    if args.action in actions:
        actions[args.action](config, db_engine, args)
    else:
        print("No action defined")
