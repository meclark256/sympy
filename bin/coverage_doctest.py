#!/usr/bin/env python

"""
Program to test that all methods/functions have at least one example
doctest.


Usage:

bin/coverage_doctest.py sympy/core

or

bin/coverage_doctest.py sympy/core/basic.py

"""

from __future__ import with_statement

import os
import re
import sys
import string
import inspect
from optparse import OptionParser

# Load color templates, used from sympy/utilities/runtests.py
color_templates = (
    ("Black", "0;30"),
    ("Red", "0;31"),
    ("Green", "0;32"),
    ("Brown", "0;33"),
    ("Blue", "0;34"),
    ("Purple", "0;35"),
    ("Cyan", "0;36"),
    ("LightGray", "0;37"),
    ("DarkGray", "1;30"),
    ("LightRed", "1;31"),
    ("LightGreen", "1;32"),
    ("Yellow", "1;33"),
    ("LightBlue", "1;34"),
    ("LightPurple", "1;35"),
    ("LightCyan", "1;36"),
    ("White", "1;37"),
)

colors = {}

for name, value in color_templates:
    colors[name] = value
c_normal = '\033[0m'
c_color = '\033[%sm'


def print_header(name, underline=None, overline=None):

    print
    print name
    if underline:
        print underline*len(name)


def print_coverage(module_path, c, c_md, c_mdt, c_idt, f, f_md, f_mdt, f_idt, score, total_doctests, total_members, verbose=False, no_color=False):

    """ Prints details (depending on verbose) of a module """

    if no_color:
        score_string = "%s%% (%s of %s)" % (score, total_doctests,
            total_members)

    elif score < 100:
        score_string = "%s%s%% (%s of %s)%s" % (c_color % (colors["Red"]), score, total_doctests, total_members, c_normal)
    else:
        score_string = "%s%s%% (%s of %s)%s" % (c_color % (colors["Green"]), score, total_doctests, total_members, c_normal)

    if verbose:
        print '\n' + '-'*70
        print module_path
        print '-'*70
    else:
        print "%s: %s" % (module_path, score_string)

    if verbose:
        print_header('CLASSES', '*')
        if not c:
            print_header('No classes found!')

        else:
            if c_md:
                print_header('Missing docstrings', '-')
                for md in c_md:
                    print '  * ' + md
            if c_mdt:
                print_header('Missing doctests', '-')
                for md in c_mdt:
                    print '  * ' + md
            if c_idt:
                # Use "# indirect doctest" in the docstring to
                # supress this warning.
                print_header('Indirect doctests', '-')
                for md in c_idt:
                    print '  * ' + md
                print '\n    Use \"# indirect doctest\" in the docstring to supress this warning'

        print_header('FUNCTIONS', '*')
        if not f:
            print_header('No functions found!')
        else:
            if f_md:
                print_header('Missing docstrings', '-')
                for md in f_md:
                    print '  * ' + md
            if f_mdt:
                print_header('Missing doctests', '-')
                for md in f_mdt:
                    print '  * ' + md
            if f_idt:
                print_header('Indirect doctests', '-')
                for md in f_idt:
                    print '  * ' + md
                print '\n    Use \"# indirect doctest\" in the docstring to supress this warning'

    if verbose:
        print '\n' + '-'*70
        print "SCORE: %s" % (score_string)
        print '-'*70


def _is_indirect(member, doc):

    """ Given string repr of doc and member checks if the member
    contains indirect documentation """

    d = member in doc
    e = 'indirect doctest' in doc
    if not d and not e:
        return True
    else:
        return False


def _get_arg_list(name, fobj):

    """ Given a function object, constructs a list of arguments
    and their defaults. Takes care of varargs and kwargs """

    trunc = 20  # Sometimes argument length can be huge

    argspec = inspect.getargspec(fobj)

    arg_list = []

    if argspec.args:
        for arg in argspec.args:
            arg_list.append(str(arg))

    arg_list.reverse()

    # Now add the defaults
    if argspec.defaults:
        rev_defaults = list(argspec.defaults).reverse()
        for i in range(len(argspec.defaults)):
            arg_list[i] = str(arg_list[i]) + '=' + str(argspec.defaults[-i])

    # Get the list in right order
    arg_list.reverse()

    # Add var args
    if argspec.varargs:
        arg_list.append(argspec.varargs)
    if argspec.keywords:
        arg_list.append(argspec.keywords)

    # Truncate long arguments
    arg_list = map(lambda x: x[:trunc], arg_list)

    # Construct the parameter string (enclosed in brackets)
    str_param = "%s(%s)" % (name, ', '.join(arg_list))

    return str_param


def get_mod_name(path, base):

    """ Gets a module name, given the path of file/dir and base
    dir of sympy """

    rel_path = os.path.relpath(path, base)

    # Remove the file extension
    rel_path, ign = os.path.splitext(rel_path)

    # Replace separators by . for module path
    file_module = ""
    h, t = os.path.split(rel_path)
    while h or t:
        if t:
            file_module = t + '.' + file_module
        h, t = os.path.split(h)

    return file_module[:-1]


def process_function(name, c_name, b_obj, mod_path, f_sk, f_md, f_mdt, f_idt, f_has_doctest, sk_list):

    """ Processes a function to get information regarding documentation.
    It is assume that the function calling this subrouting has already
    verified that it is a valid module function """

    if name in sk_list:
        return False, False

    # We add in the end, as inspect.getsourcelines is slow
    add_md = False
    add_mdt = False
    add_idt = False
    f_doctest = False
    function = False

    if inspect.isclass(b_obj):
        obj = getattr(b_obj, name)
    else:
        obj = b_obj

    # Check function for various categories
    if inspect.isclass(b_obj):
        full_name = _get_arg_list(c_name + '.' + name, obj)
    else:
        full_name = _get_arg_list(name, obj)
    if name.startswith('_'):
        f_sk.append(full_name)
    else:
        if not obj.__doc__:
            add_md = True
        elif not '>>>' in obj.__doc__:
            add_mdt = True
        elif _is_indirect(name, obj.__doc__):
            add_idt = True
        else:
            f_doctest = True

        function = True

    if add_md or add_mdt or add_idt:

        try:
            line_no = inspect.getsourcelines(obj)[1]
        except IOError:
            # Raised when source does not exist
            # which means the function is not there.
            return False, False

        full_name = "LINE %d: %s" % (line_no, full_name)
        if add_md:
            f_md.append(full_name)
        elif add_mdt:
            f_mdt.append(full_name)
        elif add_idt:
            f_idt.append(full_name)

    return f_doctest, function


def process_class(c_name, obj, c_sk, c_md, c_mdt, c_idt, c_has_doctest):

    """ Extracts information about the class regarding documentation.
    It is assumed that the function calling this subroutine has already
    checked that the class is valid. """

    # Skip class case
    if c_name.startswith('_'):
        c_sk.append(c_name)
        return False, False, None

    c = False
    c_dt = False
    # Get the line number of class
    try:
        source, line_no = inspect.getsourcelines(obj)
    except IOError:
        # Raised when source does not exist
        # which means the class is not there.
        return False, False, None

    c = True
    full_name = "LINE %d: %s" % (line_no, c_name)
    if not obj.__doc__:
        c_md.append(full_name)
    elif not '>>>' in obj.__doc__:
        c_mdt.append(full_name)
    elif _is_indirect(c_name, obj.__doc__):
        c_idt.append(full_name)
    else:
        c_dt = True
        c_has_doctest.append(full_name)

    return c_dt, c, source


def coverage(module_path, verbose=False, no_color=False):

    """ Given a module path, builds an index of all classes and functions
    contained. It then goes through each of the classes/functions to get
    the docstring and doctest coverage of the module. """

    # Import the package and find membmers
    m = None
    try:
        __import__(module_path)
        m = sys.modules[module_path]
    except Exception, a:
        # Most likely cause, absence of __init__
        print "%s could not be loaded due to %s." % (module_path, repr(a))
        return 0, 0

    c_skipped = []
    c_md = []
    c_mdt = []
    c_has_doctest = []
    c_idt = []
    classes = 0
    c_doctests = 0

    f_skipped = []
    f_md = []
    f_mdt = []
    f_has_doctest = []
    f_idt = []
    functions = 0
    f_doctests = 0

    skip_members = ['__abstractmethods__']

    # Get the list of members
    m_members = dir(m)
    for member in m_members:

        # Check for skipped functions first, they throw nasty errors
        # when combined with getattr
        if member in skip_members:
            continue

        # Identify if the member (class/def) a part of this module
        obj = getattr(m, member)
        obj_mod = inspect.getmodule(obj)

        # Function not a part of this module
        if not obj_mod or not obj_mod.__name__ == module_path:
            continue

        # If it's a function
        if inspect.isfunction(obj) or inspect.ismethod(obj):

            f_dt, f = process_function(member, '', obj, module_path, f_skipped, f_md, f_mdt, f_idt, f_has_doctest, skip_members)
            if f:
                functions += 1
            if f_dt:
                f_doctests += 1

        # If it's a class, look at it's methods too
        elif inspect.isclass(obj):

            # Process the class first
            c_dt, c, source = process_class(member, obj, c_skipped, c_md, c_mdt, c_idt, c_has_doctest)
            if not c:
                continue
            else:
                classes += 1
            if c_dt:
                c_doctests += 1

            # Iterate through it's members
            for f_name in obj.__dict__:

                if f_name in skip_members or f_name.startswith('_'):
                    continue

                # Check if def funcname appears in source
                if not ("def " + f_name) in ' '.join(source):
                    continue

                # Identify the module of the current class member
                f_obj = getattr(obj, f_name)
                obj_mod = inspect.getmodule(f_obj)

                # Function not a part of this module
                if not obj_mod or not obj_mod.__name__ == module_path:
                    continue

                # If it's a function
                if inspect.isfunction(f_obj) or inspect.ismethod(f_obj):

                    f_dt, f = process_function(f_name, member, obj, module_path, f_skipped, f_md, f_mdt, f_idt, f_has_doctest, skip_members)
                    if f:
                        functions += 1
                    if f_dt:
                        f_doctests += 1

    # Evaluate the percent coverage
    total_doctests = c_doctests + f_doctests
    total_members = classes + functions
    if total_members:
        score = 100 * float(total_doctests) / (total_members)
    else:
        score = 100
    score = int(score)

    # Sort functions/classes by line number
    c_md = sorted(c_md, key=lambda x: int(x.split()[1][:-1]))
    c_mdt = sorted(c_mdt, key=lambda x: int(x.split()[1][:-1]))
    c_idt = sorted(c_idt, key=lambda x: int(x.split()[1][:-1]))

    f_md = sorted(f_md, key=lambda x: int(x.split()[1][:-1]))
    f_mdt = sorted(f_mdt, key=lambda x: int(x.split()[1][:-1]))
    f_idt = sorted(f_idt, key=lambda x: int(x.split()[1][:-1]))

    print_coverage(module_path, classes, c_md, c_mdt, c_idt, functions, f_md, f_mdt, f_idt, score, total_doctests, total_members, verbose, no_color)

    return total_doctests, total_members


def go(sympy_top, file, verbose=False, no_color=False, exact=True):

    if os.path.isdir(file):
        doctests, num_functions = 0, 0
        for F in os.listdir(file):
            _doctests, _num_functions = go(sympy_top, '%s/%s' % (file, F), verbose, no_color, exact=False)
            doctests += _doctests
            num_functions += _num_functions
        return doctests, num_functions
    if not (file.endswith('.py') or file.endswith('.pyx')) or \
        file.endswith('__init__.py') or \
            not exact and ('test_' in file or 'bench_' in file):
        return 0, 0
    if not os.path.exists(file):
        print "File %s does not exist." % file
        sys.exit(1)

    # Relpath for constructing the module name
    return coverage(get_mod_name(file, sympy_top), verbose, no_color)


if __name__ == "__main__":

    bintest_dir = os.path.abspath(os.path.dirname(__file__))   # bin/cover...
    sympy_top = os.path.split(bintest_dir)[0]      # ../
    sympy_dir = os.path.join(sympy_top, 'sympy')  # ../sympy/
    if os.path.isdir(sympy_dir):
        sys.path.insert(0, sympy_top)

    usage = "usage: ./bin/doctest_coverage.py PATH"

    parser = OptionParser(
        description=__doc__,
        usage=usage,
    )

    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
            default=False)
    parser.add_option("--no-color", action="store_true", dest="no_color", help="use no colors", default=False)

    options, args = parser.parse_args()

    # If no arguments, then run script on sympy/
    if len(args) == 0:
        args = [os.path.join(sympy_top, 'sympy')]

    for file in args:
        file = os.path.normpath(file)
        print 'DOCTEST COVERAGE for %s' % (file)
        print '='*70
        print
        doctests, num_functions = go(sympy_top, file, options.verbose, options.no_color)
        if num_functions == 0:
            score = 100
        else:
            score = 100 * float(doctests) / num_functions
            score = int(score)
        print
        print '='*70

        if options.no_color:
            print "TOTAL SCORE for %s: %s%% (%s of %s)" % \
                (get_mod_name(file, sympy_top), score, doctests, num_functions)

        elif score < 100:
            print "TOTAL SCORE for %s: %s%s%% (%s of %s)%s" % \
                (get_mod_name(file, sympy_top), c_color % (colors["Red"]),
                score, doctests, num_functions, c_normal)

        else:
            print "TOTAL SCORE for %s: %s%s%% (%s of %s)%s" % \
                (get_mod_name(file, sympy_top), c_color % (colors["Green"]),
                score, doctests, num_functions, c_normal)

        print
