import argparse
import os
import tempfile
import zipfile
from PIL import Image
import gifextract


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Create Android bootanimation.zip from .gif or bunch "
                    "of images")

    parser.add_argument("source", type=str, default="",
        help="Absolute path to the GIF file or folder with images."
             "Expected image name format: xxxx-001.png"
             "Where:"
             "xxx - some image name;"
             "001 - image number.")

    parser.add_argument("width", type=int, default=720,
                        help="Width of result images in pixels. "
                             "You should use width of the device screen")

    parser.add_argument("height", type=int, default=1280,
                        help="Height of result images in pixels. "
                             "You should use height of the device screen")

    parser.add_argument("fps", type=int, default=24,
                        help="FPS (Frames Per Second) for animation")

    parser.add_argument("save_to", default="",
                        help="path to the folder where result images should "
                             "be saved")

    parser.add_argument("-zip", action='store_true',
                        help="create bootanimation.zip with result images")

    args = parser.parse_args()
    return args.source, args.width, args.height, args.fps, args.save_to, args.zip


def check_args(t_source, t_width, t_height, t_fps, t_save_to, t_zip):
    result = True
    if len(t_source) <= 0:
        print("Error: source path is empty")
        result = False

    if os.path.exists(t_source) is False:
        print("Error: path '{}' do not exist".format(t_source))
        result = False

    if t_width <= 0:
        print("Error: width is too small: " + str(t_width))
        result = False

    if t_height <= 0:
        print("Error: height is too small: " + str(t_height))
        result = False

    if t_fps <= 0:
        print("Error: fps is too small: " + str(t_fps))
        result = False

    if t_fps <= 0:
        print("Error: fps is too small: " + str(t_fps))
        result = False

    if len(t_save_to) <= 0:
        print("Error: save_to path is empty")
        result = False

    return result


def main(t_source, t_width, t_height, t_fps, t_save_to, t_zip):
    source_dir = ""
    temp_dir = None
    if os.path.isdir(t_source):
        source_dir = t_source
    elif os.path.isfile(t_source) and get_extension(t_source) == "gif":
        temp_dir = tempfile.TemporaryDirectory()
        gifextract.processImage(t_source, temp_dir.name)
        source_dir = temp_dir.name
    else:
        print("Error: invalid source path: " + t_source)
        return

    images = get_images_paths(source_dir)
    if len(images) <= 0:
        print("Error: no images to process")
        return

    if not os.path.exists(t_save_to):
        os.makedirs(t_save_to)

    path_to_desc_file = create_desc_file(t_save_to, t_width, t_height, t_fps)

    dir_for_images = t_save_to + "/part0"
    if not os.path.exists(dir_for_images):
        os.makedirs(dir_for_images)

    count = 0
    for img in images:
        count = transform_images(img, count, t_width, t_height, dir_for_images)

    with open(path_to_desc_file, "a") as f:
        print("p 1 0 part0", file=f)

    if t_zip is True:
        zip_file = zipfile.ZipFile(t_save_to + "/bootanimation.zip", mode="w",
                                   compression=zipfile.ZIP_STORED)

        zip_file.write(path_to_desc_file,
                       arcname=os.path.basename(path_to_desc_file))

        zip_dir(dir_for_images, zip_file)
        zip_file.close()

    print("Done")


def get_extension(t_path):
    path_parts = str.split(t_path, '.')
    extension = path_parts[-1:][0]
    extension = extension.lower()
    return extension


def get_images_paths(t_folder):
    if not os.path.isdir(t_folder):
        return list()

    image_extensions = ("jpg", "jpeg", "bmp", "png", "tiff")
    images = list()
    entries = os.listdir(t_folder)
    for entry in entries:
        file_path = os.path.join(t_folder, entry)
        extension = get_extension(file_path)
        if os.path.isfile(file_path) and extension in image_extensions:
            images.append(file_path)

    images.sort()
    return images


def create_desc_file(t_folder, t_width, t_height, t_fps):
    file_name = t_folder + "/desc.txt"
    fd = open(file_name, mode="w+")
    print("{} {} {}".format(t_width, t_height, t_fps), file=fd)
    return file_name


def transform_images(t_img_path, t_count, t_width, t_height, t_save_to_path):
    original_img = Image.open(t_img_path)

    # Scale image
    width_percent = (t_width / float(original_img.width))
    height_size = int((float(original_img.height) * float(width_percent)))
    original_img = original_img.resize((t_width, height_size), Image.LANCZOS)

    result_image = Image.new("RGB", (t_width, t_height), "white")

    width_pos = 0
    height_pos = int(t_height / 2 - original_img.height / 2)
    result_image.paste(original_img, (width_pos, height_pos))

    result_img_name = "{0:0{width}}.png".format(t_count, width=5)
    result_img_path = t_save_to_path + "/" + result_img_name
    result_image.save(result_img_path)
    t_count += 1
    return t_count


def zip_dir(t_path, t_zip_file):
    path_head, last_dir = os.path.split(t_path)
    images = get_images_paths(t_path)
    for img in images:
        img_path_in_zip = last_dir + "/" + os.path.basename(img)
        t_zip_file.write(img, arcname=img_path_in_zip,
                         compress_type=zipfile.ZIP_STORED)


if __name__ == '__main__':
    arguments = parse_arguments()
    if check_args(*arguments) is True:
        main(*arguments)
