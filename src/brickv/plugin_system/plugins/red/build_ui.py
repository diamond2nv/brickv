#!/usr/bin/env python

import os

os.system("pyuic4 -o ui_red.py ui/red.ui")
os.system("pyuic4 -o ui_red_tab_overview.py ui/red_tab_overview.ui")
os.system("pyuic4 -o ui_red_tab_settings.py ui/red_tab_settings.ui")
os.system("pyuic4 -o ui_red_tab_program.py ui/red_tab_program.ui")
os.system("pyuic4 -o ui_red_tab_console.py ui/red_tab_console.ui")
os.system("pyuic4 -o ui_red_tab_versions.py ui/red_tab_versions.ui")
os.system("pyuic4 -o ui_red_tab_extension.py ui/red_tab_extension.ui")
os.system("pyuic4 -o ui_red_tab_extension_ethernet.py ui/red_tab_extension_ethernet.ui")
os.system("pyuic4 -o ui_program_info.py ui/program_info.ui")
os.system("pyuic4 -o ui_program_page_general.py ui/program_page_general.ui")
os.system("pyuic4 -o ui_program_page_files.py ui/program_page_files.ui")
os.system("pyuic4 -o ui_program_page_java.py ui/program_page_java.ui")
os.system("pyuic4 -o ui_program_page_python.py ui/program_page_python.ui")
os.system("pyuic4 -o ui_program_page_ruby.py ui/program_page_ruby.ui")
os.system("pyuic4 -o ui_program_page_arguments.py ui/program_page_arguments.ui")
os.system("pyuic4 -o ui_program_page_stdio.py ui/program_page_stdio.ui")
os.system("pyuic4 -o ui_program_page_schedule.py ui/program_page_schedule.ui")
os.system("pyuic4 -o ui_program_page_summary.py ui/program_page_summary.ui")
os.system("pyuic4 -o ui_program_page_upload.py ui/program_page_upload.ui")
os.system("python build_scripts.py")
