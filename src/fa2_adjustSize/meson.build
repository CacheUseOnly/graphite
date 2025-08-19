# Find Python to get the extension suffix
python = import('python').find_installation()
python_version = python.language_version().replace('.', '')
host_machine_system = host_machine.system()

# Determine the expected .so filename pattern
arch_suffix = host_machine.cpu_family() == 'x86_64' ? 'x86_64-linux-gnu' : host_machine.cpu_family() + '-linux-gnu'
so_pattern = 'fa2util.cpython-@0@-@1@.so'.format(python_version, arch_suffix)

fa2util = custom_target(
  so_pattern,
  input: ['setup.py', 'fa2util.py'],
  output: so_pattern,
  command: [
    python.full_path(),
    '@INPUT0@',
    '@INPUT1@',
    'build_ext',
    '--build-lib',
    '@OUTDIR@',
    '--build-temp',
    '@OUTDIR@',
  ],
  build_by_default: true,
  install: true,
  install_dir: get_option('datadir') / 'Graphite' / 'graphite' / 'fa2_adjustSize',
)