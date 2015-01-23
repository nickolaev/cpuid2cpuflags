#!/usr/bin/env python
# vim:se fileencoding=utf8
# (c) 2015 Michał Górny
# Released under the 2-clause BSD license

import collections, errno, os, os.path, re, sys

def main(*argv):
	if 'PORTDIR' in os.environ:
		portdir = os.environ['PORTDIR']
	else:
		try:
			import portage
		except ImportError:
			return '''
Unable to import portage modules in order to determine the Gentoo
repository location. Please either make sure to run the script with
a Python implementation supported by your Portage installation or
export PORTDIR variable before running the script.
'''
		else:
			trees = portage.create_trees(
					config_root = os.environ.get('PORTAGE_CONFIGROOT'),
					target_root = os.environ.get('ROOT'))
			tree = trees[max(trees)]
			portdir = tree['porttree'].dbapi.repositories.get_location_for_name('gentoo')

	# dict of cpuinfo -> flag mappings
	flag_dict = collections.defaultdict(list)

	desc = os.path.join(portdir, 'profiles', 'desc', 'cpu_flags_x86.desc')
	# flag - description ; discards empty lines and comments
	l_regexp = re.compile(r'^(?P<flag>[a-z0-9_]+)\s+-\s+(?P<desc>.+)$')
	# [cpuinfo-flag] ; [] are discarded for easy use
	cpuinfo_regexp = re.compile(r'(?<=\[).+?(?=\])')
	try:
		with open(desc, 'r') as f:
			for l in f:
				m = l_regexp.match(l)
				if m:
					# grep for any [cpuinfo] or [cpuinfo2]
					flags = cpuinfo_regexp.findall(l)
					for fl in flags:
						flag_dict[fl].append(m.group('flag'))
					# fallback to exact flag match
					if not flags:
						flag_dict[m.group('flag')].append(m.group('flag'))
	except OSError as e:
		if e.errno == errno.ENOENT:
			return '''
Unable to find the profiles/desc/cpu_flags_x86.desc file that is needed
to determine the correct CPU_FLAGS_X86 values. Please either update
your Gentoo repostiory checkout ('emerge --sync') or export PORTDIR
to a (newer) Gentoo repository checkout.

The current PORTDIR is: %s
''' % portdir

	out = set()

	flags_regexp = re.compile(r'^flags\s+:\s+(?P<flags>.*)$')
	with open('/proc/cpuinfo', 'r') as f:
		for l in f:
			m = flags_regexp.match(l)
			if m:
				for fl in m.group('flags').split():
					if fl in flag_dict:
						out.update(flag_dict[fl])
				break

	print('CPU_FLAGS_X86="%s"' % ' '.join(sorted(out)))
	return 0

if __name__ == '__main__':
	sys.exit(main(*sys.argv[1:]))