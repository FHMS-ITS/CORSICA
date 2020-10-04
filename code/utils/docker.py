from utils.log import _info
import docker


def build_docker(image_name, dockerfile_path):
    docker_client = docker.from_env()
    if not any(image_name in str(s) for s in docker_client.images.list()):
        _info("corsica.dockr.sel", "Building docker image {}...".format(image_name))
        docker_client.images.build(path=dockerfile_path, tag="{}:latest".format(image_name))
        _info("corsica.dockr.sel", "Finished building docker image {}...".format(image_name))


def pull_image(image_name, tag="latest"):
    #_info("corsica.dockr.sel", 'Pulling docker image {}:{}'.format(image_name, tag))
    docker_client = docker.from_env()
    docker_client.images.pull(image_name, tag)
    #_info("corsica.dockr.sel", 'Successfully pulled docker image {}:{}'.format(image_name, tag))

def get_images(image_name):
    docker_client = docker.from_env()
    return docker_client.images.list("selenium/*")


def get_images_tags(image_name):
    images = get_images(image_name)
    ret = []
    for image in images:
        if image.tags:
            ret.append(image.tags[0])
    return ret
