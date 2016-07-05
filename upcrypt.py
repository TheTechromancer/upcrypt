#!/usr/bin/python3
'''
upcrypt.py

Batch-encrypt files using 7zip

Written and tested for Python 3.5.1

TODO:
continue debugging

'''

import os
import re
import argparse
import threading
import subprocess as sp
from sys import stderr, stdout, exit
from multiprocessing import cpu_count

print_lock = threading.Lock()		# keeps output clean
devnull = open(os.devnull, 'wb')	# used to discard shell output
cleanup_dirs = []

### DEFAULTS ###

e_suffix = '_encrypted'	# append to encrypted folders
d_suffix = '_decrypted'	# append to decrypted folders
std_out = devnull	# don't display output of shell commands

# split large files into pieces of this size
split_size = None	# set to 'None' if splitting archives into chunks is not desired



### FUNCTIONS ###

def _inventory(paths, wrap=False, decrypting=False):
	'''
	takes:		list of paths
	returns:	tuple - (basename, abspath, relpath)
	purpose:	take inventory of files to be encrypted
	'''

	inventory = {}

	verbose_print("\n[+] Taking inventory of files")

	for path in paths:

		inventory[path] = []

		try:

			assert os.path.exists(path)

			if os.path.isfile(path) or (wrap and not decrypting):
				# don't worry about finding individual files

				basename = os.path.basename(path)
				abspath = path
				relpath = os.path.relpath(path)

				inventory[path].append((basename, abspath, relpath))

			else:
				# discover all files

				for d in os.walk(path):
					for basename in d[2]:
						abspath = os.path.join(d[0], basename)
						relpath = os.path.relpath(abspath, start=path)

						inventory[path].append((basename, abspath, relpath))

			verbose_print("[+]  Source file: {}".format(relpath))
			verbose_print("[+]   path: {}\n[+]   basename: {}\n[+]   abspath: {}\n[+]   relpath: {}".format(path, basename, abspath, relpath))

		except AssertionError:
			error_print("{} does not exist.".format(path))
			continue

	return inventory



def _make_jobs(inventory, dst_path, pwd, decrypting=False, wrapping=False):
	'''
	takes:		inventory dict (basename, abspath, relpath), destination path, password, and decrypting (True or False)
	returns:	tuple for _encrypt - (basename, src, dst, password)
	purpose:	prepares destination folders and filenames
	'''

	jobs = []

	verbose_print("\n[+] Creating list of jobs")

	if decrypting:
		r = re.compile('\.\d\d\d$') # matches *.001, *.002, etc.


	for p in inventory.keys():

		# determine destination path
		if not dst_path:

			out_dir = os.path.split(p)[0]

			if os.path.isdir(p) and not wrapping:

				a, b = os.path.split(p)

				# adding suffix to folder helps avoid confusion over which is encrypted
				if decrypting:
					out_dir = os.path.join(a, '{}{}'.format(b, d_suffix))

				else:
					out_dir = os.path.join(a, '{}{}'.format(b, e_suffix))

				cleanup_dirs.append(out_dir) # used for clean_encrypted function

				if os.path.exists(out_dir):
					error_print("{} already exists.  Please rename it or use a different destination.".format(out_dir))
					exit(1)

		else:
			out_dir = dst_path


		for i in inventory[p]:

			basename, src, relpath = i

			# determine destination filename
			# if archives are split, only use the first file (weeds out *.002 and up)
			if decrypting:

				if r.findall(basename):
					if basename.endswith('.001'):
						basename = basename[:-4]
					else:
						continue

				rel_dir = os.path.split(relpath)[0]
				dst = os.path.join(out_dir, rel_dir)
				dst_dir = os.path.join(out_dir, rel_dir)

			else:

				basename = '{}.7z'.format(basename)
				rel_dir = os.path.split(relpath)[0]

				dst = os.path.join(out_dir, rel_dir, basename)
				dst_dir = os.path.split(dst)[0]

			if not dir_check(dst_dir):
				continue

			verbose_print("[+]  Destination file: {}".format(relpath))
			verbose_print("[+]   basename: {}\n[+]   src: {}\n[+]   dst: {}".format(basename, src, dst))

			jobs.append((basename, src, dst, pwd))

	return jobs



def clean_encrypted(dir_path):
	'''
	removes '.001' after files if they weren't actually split
	'''

	verbose_print("\n[+] Cleaning up encrypted files in {}".format(dir_path))

	w = os.walk(dir_path)

	e = {} # keeps track of how many pieces each file has

	for d in w:
		for f in d[2]:
			filename = os.path.join(d[0], f)
			if filename.endswith(('.001', '.002')):
				basename = filename[:-4]
				if basename in e:
					e[basename] += 1
				else:
					e[basename] = 1
			else:
				continue

	for new_filename in e:
		if e[new_filename] == 1:
			old_filename = '{}.001'.format(new_filename)
			verbose_print("[+]  Renaming {} to {}".format(old_filename, new_filename))
			os.rename(old_filename, new_filename)



def dir_check(dir_path):
	'''
	checks if a directory exists and creates it doesn't
	'''
	verbose_print("[*] Checking directory {}".format(dir_path))

	if dir_path.endswith('.7z'):
		dir_path = dir_path[:-3]

	try:
		os.makedirs(dir_path)

	except NotADirectoryError:
		error_print("File already exists with name {}".format(dir_path))
		return 0

	except FileExistsError:
		verbose_print("[*] Directory {} already exists".format(dir_path))

	return 1



def verbose_print(*a):
	return None



def error_print(a):
	with print_lock:
		stderr.write('\n[!]	{}\n'.format(str(a)))




### CLASSES ###

class crypt(threading.Thread):

	def __init__(self, basename, src, dst, pwd, thread_lock, decrypting=False, split=False):
		super().__init__()
		self.basename = basename
		self.src = src
		self.dst = dst
		self.pwd = pwd
		self.thread_lock = thread_lock
		self.decrypting = decrypting
		self.split = split

	def run(self):

		with self.thread_lock:
			if self.decrypting:
				self._decrypt()
			else:
				self._encrypt()

	def _encrypt(self):
		'''
		takes:		basename, absolute source and destination paths, and password
		does:		encrypts all the things!
		'''
		try:

			# set up file-splitting argument
			if self.split:
				split_str = '-v{}'.format(self.split)

			else:
				split_str = ''

			cmd_lst = ['7za', 'a', split_str, '-p{}'.format(self.pwd), self.dst, self.src]

			# print shell command
			verbose_print("[+] {}".format(' '.join(cmd_lst)))

			sp.run(cmd_lst, stdout=std_out, check=True)

		except sp.CalledProcessError as e:
			error_print("Error in _encrypt function: {}".format(str(e.output)))
			error_print("Cannot encrypt {}".format(self.basename))



	def _decrypt(self):
		'''
		takes:		basename, archive, destination directory, and password
		does:		decrypts all the things!
		'''
		try:

			cmd_lst = ['7za', 'x', '-o{}'.format(self.dst), '-p{}'.format(self.pwd), self.src]

			# print shell command
			verbose_print("[+] {}".format(' '.join(cmd_lst)))

			sp.run(cmd_lst, stdout=std_out, check=True)

		except sp.CalledProcessError as e:
			error_print("Error in _decrypt function: {}".format(str(e.output)))
			error_print("Cannot decrypt {}.  Double-check password.".format(self.basename))




### ARGS ###

if __name__ == '__main__':

	parser = argparse.ArgumentParser(
		description="Batch-encrypts files using 7-zip.\
		To 'Process' means to encrypt or decrypt, depending on which it's doing.")
	parser.add_argument('files',				type=os.path.abspath,	nargs='*',			metavar='FILES',	help="Files or directories to process")
	parser.add_argument('-d', '--decrypt',		action='store_true',											help="Decrypt rather than encrypt")
	parser.add_argument('-p', '--password',		type=str,	required=True,					metavar='PASS',		help="Password to use for encryption/decryption")
	parser.add_argument('-o', '--out-dir',		type=os.path.abspath,						metavar='DIR',		help="Where to put processed files")
	parser.add_argument('-w', '--wrap',			action='store_true',											help="Zip directories into single file - don't encrypt individually")
	parser.add_argument('-t', '--threads',		type=int,			default=cpu_count(),	metavar='INT',		help="Number of CPU cores to use.  Default is all.")
	parser.add_argument('--split',				type=str,			default=split_size,		metavar='SIZE',		help="Split into volumes of SIZE.  Default is {}.  Useful for circumventing filesize limitations. ;)".format(str(split_size)))
	parser.add_argument('-v', '--verbose',		action='store_true',											help="Print what is happening.  Note: sets threads to 1.")

	try:
		options = parser.parse_args()

		# verbose function does nothing if verbose not set
		if options.verbose:
			def verbose_print(a):
				with print_lock:
					print(str(a))
			options.threads = 1 # prevents 7z shell output from mixing together
			std_out = None

		if options.decrypt:
			options.wrap = None

		thread_lock = threading.Semaphore(options.threads)
		jobs = []

		for j in _make_jobs(_inventory(options.files, options.wrap, options.decrypt),\
			options.out_dir, options.password, options.decrypt, options.wrap):

			jobs.append(crypt(j[0], j[1], j[2], j[3], thread_lock, options.decrypt, options.split))

		for job in jobs:
			job.start()

		for job in jobs:
			job.join()

		verbose_print("[*] List of directories to be cleaned: {}".format(str(cleanup_dirs)))
		for d in cleanup_dirs:
			clean_encrypted(d)


	except argparse.ArgumentError:
		error_print("Check your syntax.  Use -h for help.\n")
		exit(2)
	except PermissionError as e:
		error_print("Permission error: {}".format(str(e)))
		exit(1)
		