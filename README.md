# SublimeKSP

A Sublime Text (versions 3 and 4) plugin for working with and compiling KSP (Kontakt Script Processor) code.

### Changes
This fork is based on [Nils Liberg's official SublimeKSP plugin, v1.11](http://nilsliberg.se/ksp/), and supports all Kontakt versions.
However, there are a number of additions and changes:

* Available in Package Control, which supports automatic updates
* Available in Visual Studio Marketplace, which supports automatic updates
* Updates to the syntax highlighting
* Support for Creator Tools GUI Designer
* Numerous additions to the preprocessor, allowing for many new features; see the [Extended Script Syntax](https://github.com/nojanath/SublimeKSP/wiki#extended-script-syntax) section of the [Wiki](https://github.com/nojanath/SublimeKSP/wiki) for more information

### Installation (Sublime Text)

* Install [Package Control](https://packagecontrol.io/installation)
* After installing Package Control and restarting Sublime Text:
  * Open the Command Palette from the Tools menu, or by pressing <kbd>Cmd</kbd><kbd>Shift</kbd><kbd>P</kbd> (macOS) or <kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>P</kbd> (Windows)
  * Type "Install Package"
  * Type "KSP" and select "KSP (Kontakt Script Processor)"
  * Press <kbd>Enter</kbd> to install
  * Restart Sublime Text

### Installation (Visual Studio Code)

* Click the Extensions tab
* Type "SublimeKSP" in the search bar
* Click the "Install" button of the search result
* Done!

### Manual Installation (Sublime Text)

To use features of SublimeKSP before official package releases:

 * If you already had SublimeKSP installed via Package Control, uninstall it before continuing further!
 * Locate Sublime Text's `Packages`folder by selecting `Preferences > Browse Packages` from the main menu
 * Clone SublimeKSP repository into this folder via Git (`git clone https://github.com/nojanath/SublimeKSP.git "KSP (Kontakt Script Processor)"`)
 * After pulling the latest changes (`git pull`), reload Sublime Text
 * If you wish to pull in latest changes without restarting Sublime Text, we recommend installing [Automatic​Package​Reloader](https://packagecontrol.io/packages/AutomaticPackageReloader)

### Contributing

Bug reports, feature requests, and especially pull requests with bug fixes and feature implementations are welcome! Let us know by [opening an issue](https://github.com/nojanath/SublimeKSP/issues) so that we can start a discussion.

Building and modifying the extension locally is fairly straightforward. For Sublime Text, all you need to do is use the manual installation as explained above. For VS Code, the main prerequisite is to have [node.js](https://nodejs.org/en/download/prebuilt-installer) installed on your machine. From there:

* Clone this repository on your hard drive
* Navigate to the repository folder from command line
* Execute `npm install` from the command line to bootstrap things required in order to build the VS Code extension
* If adding new built-in data (for example, new engine parameters or new functions introduced to KSP), make sure to run the `update-builtins.py` script from `dev/` folder!
* When adding new snippets, make sure there is _no_ newline after the `CDATA[` part, as this would misbehave in VS Code (Sublime Text disregards this potential extra newline, VS Code does not)
* To build the VSIX extension, simply run `build-vsix.sh` from Bash shell or `build-vsix.bat` from Windows command line

### Compiling From The Command Line

SublimeKSP compiler can also be executed from the command line by simply running `ksp_compiler.py` with the appropriate source (and optionally output) file path(s), along with optional compiler switches.
For this you need to use the manual installation of SublimeKSP, in order to have direct access to `ksp_compiler.py`. To execute a compilation of a file, it is as simple as typing:

```
> python ksp_compiler.py "<source-file-path>"
```

Various compiler options from SublimeKSP's Tools menu are also available. All of them are set to false if not used, and by including them in the command line, they are set to true:

```
ksp_compiler.py [-h] [-c] [-v] [-e] [-o] [-t] [-d] source_file [output_file]

positional arguments:
  source_file
  output_file

optional arguments:
  -h, --help                               show this help message and exit
  -f, --force                              force all specified compiler options, overriding any compile_with pragma directives from the script
  -c, --compact                            remove indents in compiled code
  -v, --compact_variables                  shorten and obfuscate variable names in compiled code
  -d, --combine_callbacks                  combines duplicate callbacks - but not functions or macros
  -e, --extra_syntax_checks                additional syntax checks during compilation
  -o, --optimize                           optimize the compiled code
  -b, --extra_branch_optimization          adds branch optimization checks earlier in compile process, allowing define constant based branching etc.
  -l, --log                                dumps the compiler output to a log file on failed compilation
  -i NUM_SPACES, --indent-size NUM_SPACES  specifies how many spaces is used for indentation, if --compact compiler option is not used
  -t, --add_compile_date                   adds the date and time comment atop the compiled code
  -x, --sanitize_exit_command              adds a dummy no-op command before every exit function call


> python ksp_compiler.py --force -c -e -o "<source-file-path>" "<target-file-path>"
```

### Updates
Updates to the plugin will be automatically installed via Package Control or Visual Studio Marketplace.

### Documentation
See the [Wiki](https://github.com/nojanath/SublimeKSP/wiki).
