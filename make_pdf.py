import argparse
import fnmatch
import os
from notebook_as_pdf import PDFExporter,notebook_to_pdf
import nbformat
import shutil
import PyPDF2
import pathlib

def parse_args():
    print('parse_args...')
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command')
    commands.required = True

    init_parser = commands.add_parser('dir')
    init_parser.set_defaults(func=convert_dir)
    init_parser.add_argument('--path', '-p')
    init_parser.add_argument('--out', '-o', default='.')
    init_parser.add_argument('--recursive', '-r', action="store_true", default=True)
    init_parser.add_argument('--include', '-i', default='')
    init_parser.add_argument('--exclude', '-e', default='')
    init_parser.add_argument('--config', '-c', default='')
    init_parser.add_argument('--clean_output', action="store_true", default=False)
    

    return parser.parse_args()

def get_file_first_name(file_name):    
    basename = os.path.basename(file_name)
    firstname = os.path.splitext(basename)[0]
    return firstname

def export_pdf(full, out_root_path, config):
    firstname = get_file_first_name(full)
    print(firstname)
    newname = firstname + '.pdf'
    pdfname = os.path.join(out_root_path, newname)
    exp = PDFExporter(config)
    if os.path.exists(pdfname):
        print(' skip exists:', full)
        return
    with open(full, 'rb') as f:
        nb = nbformat.reads(f.read(), as_version=4)
        ob = exp.from_notebook_node(nb)
        with open(pdfname, 'wb+') as fw:
            fw.write(ob[0])

def join_pdf(path, output_filename='all_in_one.pdf'):
    with os.scandir(path) as it:
        pdf_merge = []
        for entry in it:
            if not fnmatch.fnmatch(entry.name, "*.pdf"):
                continue
            if entry.name == output_filename:
                continue
            pdf_merge.append(os.path.join(path, entry.name))
    pdf_merge.sort()
    merger = PyPDF2.PdfFileMerger()
    for f in pdf_merge:
        firstname = get_file_first_name(f)
        merger.append(PyPDF2.PdfFileReader(f), bookmark=firstname)
    with open(os.path.join(path, output_filename), 'wb') as writer:
        merger.write(writer)
    

    return
    if len(pdf_merge) > 0:
        pdf_writer = PyPDF2.PdfFileWriter()
        for f in pdf_merge:
            with open(f, 'rb') as reader:
                pdf_reader = PyPDF2.PdfFileReader(reader)
                for pageNum in range(pdf_reader.numPages):
                    pageObj = pdf_reader.getPage(pageNum)
                    pdf_writer.addPage(pageObj)
        
        with open(os.path.join(path, output_filename), 'wb') as writer:
            pdf_writer.write(writer)

                


def in_filter(full, filters) -> bool:
    if fnmatch.fnmatch(full, filters):
        return True
    return False

def working_tree(path, recursive, include, exclude, tree):
    with os.scandir(path) as it:
        for entry in it:
            full = os.path.join(path, entry.name)
            if entry.is_file (follow_symlinks=False):
                if include != '' and not in_filter(entry.name, include):
                    continue
                if exclude != '' and in_filter(entry.name, exclude):
                    continue
                tree.append(full)
            elif entry.is_dir (follow_symlinks=False) and recursive:
                if exclude != '' and in_filter(entry.name, exclude):
                    continue
                working_tree(full, recursive, include, exclude, tree)
    
def print_tree(tree):
    print('tree:')
    for full in tree:
        print(' ', full)

def convert_dir(args):
    path = args.path
    recursive = args.recursive
    #filters = set(args.filter.split(','))
    include = args.include
    exclude = args.exclude
    outpath = args.out
    clean_output = args.clean_output

    print('convert folder from ', path)
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    source_files = []
    working_tree(path, recursive, include, exclude, source_files)
    print_tree(source_files)

    if clean_output and os.path.exists(outpath):
        shutil.rmtree(outpath)
        
    pathlib.Path(outpath).mkdir(parents=False, exist_ok=True) 

    for full in source_files:
        export_pdf(full, outpath, None)
    
    join_pdf(outpath)

def main():
    print('main...')
    args = parse_args()
    args.func(args)

#if __name__ == '__main__':
main()