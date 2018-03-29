import os
import codecs
import re


def year_from_root(root_url):
    return int(root_url[-4:])


def index_files():
    findable_files = []

    for root, _, files in os.walk("./Past Papers"):
        if len(files) == 0:
            continue

        year = year_from_root(root)

        for file in files:
            file_name, exam_extention = os.path.splitext(file)
            if exam_extention == ".pdf_txt":
                findable_files.append(
                    (file_name, year, os.path.join(root, file)))

    return findable_files


# https://stackoverflow.com/questions/3862010/is-there-a-generator-version-of-string-split-in-python
# generator object for iterating over words in a string.
def word_iter(text):
    return (x.group(0) for x in re.finditer(r"\S+", text))


def matching_elements(token, val):
    return sum(1 if token[i] == val[i] else 0 for i in range(len(val)))


# Because the thing that read images->text might occasionally incorrectly read a letter
# we're gonna say if you match all but 1 characters from token2 against
# token1 then that's a match
def lossy_compare(token, word):
    threshold = max(len(token) - 1, 1)
    for i in range(0, max(1, len(word) - len(token) + 1)):
        matches = matching_elements(token, word[i:i + len(token)])
        if matches >= threshold:
            return True
    return False


def search_exam_paper(pages, tokens):
    results = {}
    for page_number, page in enumerate(pages, 2):
        if page.isspace():
            continue

        matches = 0
        for word in word_iter(page):
            for token in tokens:
                if lossy_compare(token, word):
                    matches += 1
                    break  # we can only match 1 token.

        if matches > 0:
            results["Page Number:" + str(page_number)] = matches
    return results


def search(files, query):
    query_token = query.split(' ')

    results = {}

    for file_name, year, url in files:
        with codecs.open(url, 'r', encoding="utf-8") as file:
            pages = file.read().split(":::::")

            matches = search_exam_paper(pages, query_token)

            if len(matches) == 0:
                continue

            if year not in results.keys():
                results[year] = {}

            results[year][file_name] = matches

    return results

# sure rank_years and rank_papers share alot of logic
# but i'm too tired to think of a clean way to merge their logic


def rank_years(matches):
    years = {}

    for year, papers in matches.items():
        frequency = 0

        for page_freq in papers.values():
            frequency += sum(freq for freq in page_freq.values())

        years[year] = frequency

    return sorted(years, key=lambda k: years[k], reverse=True)


def rank_papers(papers):
    p_freqs = {}

    for paper_name, pages in papers.items():
        p_freqs[paper_name] = sum(freq for freq in pages.values())

    return sorted(p_freqs, key=lambda k: p_freqs[k], reverse=True)


def output_matches(matches):
    ranked_years = rank_years(matches)
    print("- Top Matches:")

    for year in ranked_years:
        papers = rank_papers(matches[year])

        print("--- Year: %d" % year)
        for paper in papers:
            print("----- Paper: %s" % paper)
            for page in matches[year][paper]:
                print("------- %s" % page)


def run_search_loop():
    searchable_files = index_files()
    while True:
        query = input('Query > ')

        if query in ["quit", "exit"]:
            break

        if len(query) < 2:
            print("length of query must be >= 2")
            continue

        matches = search(searchable_files, query)

        if len(matches) == 0:
            print("No Matches found for query %s" % query)
            continue

        output_matches(matches)


if __name__ == "__main__":
    if not os.path.exists("./Past Papers"):
        print("Cannot find Past Papers directory")
    else:
        run_search_loop()
