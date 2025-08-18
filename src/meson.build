pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'graphite'
gnome = import('gnome')

gnome.compile_resources('graphite',
  'graphite.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

conf = configuration_data()
conf.set('PYTHON', import('python').find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)
conf.set('APPID', 'io.github.cacheuseonly.graphite')

configure_file(
  input: 'graphite.in',
  output: 'graphite',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

apt_graph_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'canvas.py',
  'utils.py',
  'panel.py',
  'loading_page.py',
  'apt_dependency.py',
  'state_manager.py',
  'search_row.py',
  'preferences.py',
]

install_data(apt_graph_sources, install_dir: moduledir)

subdir('fa2_adjustSize')
install_subdir('fa2_adjustSize', 
               install_dir: moduledir,
               exclude_files: [
                '*.c',
                'meson.build',
                'setup.py',
                '.gitignore',
               ],
               exclude_directories: ['build']
               )
