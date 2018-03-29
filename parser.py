from PIL import Image
import pytesseract
import os
import pdf2image
import shutil
import codecs
from collections import deque
import multiprocessing
import multiprocessing.pool
import time

# Altering the process pool so we can have daemonic processes.
# https://stackoverflow.com/questions/6974695/python-process-pool-non-daemonic


class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)

# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.


class MyPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess


def process_file(png_url):
    return pytesseract.image_to_string(Image.open(png_url))


def read_exam_paper(paper):
    if not os.path.exists(paper):
        raise Exception("no paper to be found here " + paper)

    exam_url, _ = os.path.splitext(paper)

    exam_name = os.path.basename(exam_url)
    out_dir = os.path.dirname(paper)

    # temp_dir gonna be a dump for all the images of the papers.
    temp_dir = os.path.join(
        out_dir, "Temp_" + exam_name)

    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    print("Converting to images ", paper)
    images = pdf2image.convert_from_path(
        paper, output_folder=temp_dir, fmt="png")

    names = (img.filename for img in images)

    print("Reading text from paper ", paper)
    sub_worker = MyPool(8)
    texts = sub_worker.map(process_file, names)
    sub_worker.close()
    sub_worker.join()

    print("Parsed ", paper)
    return list(texts)


def enumerate_exam_papers(papers_dir):
    exam_papers = deque()
    for root, _, files in os.walk(papers_dir):
        if len(files) == 0:
            continue  # we only want directories with files in.

        for file in files:
            exam_papers.append(os.path.join(root, file))

    return list(exam_papers)


def parse_exam_paper(paper_url):
    return (paper_url, read_exam_paper(paper_url))


def cleanup(papers_url, remove_all=False):
    time.sleep(0.05)

    for (root, dirs, files) in os.walk(papers_url):
        for dir in dirs:
            if dir.startswith("Temp_"):
                shutil.rmtree(os.path.join(root, dir))
        if not remove_all:
            continue

        for file in files:
            if file.endswith(".pdf_txt"):
                os.remove(os.path.join(root, file))

    time.sleep(0.05)


def read_exam_papers(papers_dir):
    cleanup(papers_dir, remove_all=True)

    main_pool = MyPool(4)

    papers = main_pool.map(
        parse_exam_paper, enumerate_exam_papers(papers_dir))

    main_pool.close()
    main_pool.join()

    for (paper_url, pages) in papers:
        with codecs.open(paper_url + "_txt", "w+", encoding="utf-8") as f:
            f.writelines("%s ::::: " % page for page in pages[1:])

    cleanup(papers_dir)


if __name__ == "__main__":
    read_exam_papers("./Past Papers")
