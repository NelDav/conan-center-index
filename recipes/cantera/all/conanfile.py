import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.scm import Version
from conan.tools.build import check_min_cppstd
from conan.tools.files import get, save, load, chdir, rename, rmdir
from conan.tools.layout import basic_layout

class canteraRecipe(ConanFile):
    name = "cantera"
    tool_requires="scons/4.3.0"
    package_type="library"
    options = {
        "shared": [True, False]
    }
    default_options = {
        "shared": False
    }

    
    # Metadata
    description = "Cantera is an open-source collection of object-oriented software tools for problems involving chemical kinetics, thermodynamics, and transport processes."
    license = "LicenseRef-Cantera"
    homepage = "https://www.cantera.org/"
    topics = ("chemical kinetics", "combustion", "thermodynamics", "reacting flows", "catalysis", "electrochemistry")
    url = "https://github.com/conan-io/conan-center-index"

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"

    @property
    def _minimum_cpp_standard(self):
        return 17

    @property
    def _compiler_required(self):
        return {
            "Visual Studio": "16",
            "msvc": "191",
            "gcc": "8",
            "clang": "7",
            "apple-clang": "11.0",
        }

    def validate(self):
        if self.info.settings.get_safe("compiler.cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)
        
        minimum_version = self._compiler_required.get(str(self.info.settings.compiler), False)
        if minimum_version:
            if Version(self.info.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(f"{self.ref} requires C++{self._minimum_cpp_standard}, which your compiler does not support.")
        else:
            self.output.warn(f"{self.ref} requires C++{self._minimum_cpp_standard}. Your compiler is unknown. Assuming it supports C++{self._minimum_cpp_standard}")

    def requirements(self):
        self.requires("boost/1.83.0", headers=True, libs=False)
        self.requires("fmt/10.1.1", transitive_headers=True)
        self.requires("yaml-cpp/0.7.0", transitive_headers=True)
        self.requires("eigen/3.4.0", transitive_headers=True)
        self.requires("sundials/5.4.0", transitive_headers=True)

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], destination=self.source_folder, strip_root=True)

    def generate(self):
        libs = ["fmt", "yaml-cpp", "eigen"]
        include_paths = []
        lib_paths = []
        for lib in libs:
            lib_info = self.dependencies[lib].cpp_info
            include_paths = include_paths + lib_info.includedirs
            lib_paths = lib_paths + lib_info.libdirs

        sundials_info = self.dependencies["sundials"].cpp_info

        opitons = {
            "libdirname": "lib",
            "python_package": "none",
            "f90_interface": "n",
            "googletest": "none",
            "versioned_shared_library": "yes",
            "prefix": self.package_folder,
            "system_fmt": 'y',
            "system_yamlcpp": 'y',
            "system_eigen": 'y',
            "system_sundials": 'y',
            "extra_inc_dirs": os.pathsep.join(include_paths),
            "extra_lib_dirs": os.pathsep.join(lib_paths),
            "boost_inc_dir": self.dependencies["boost"].cpp_info.includedirs[0],
            "sundials_include": sundials_info.includedirs[0],
            "sundials_libdir": sundials_info.libdirs[0]
        }

        if self.settings.os == "Windows":
            opitons["toolchain"] = "msvc"

        if self.settings.build_type == "Debug":
            opitons["optimize"] = "no"
        else:
            opitons["debug"] = "no"

        escape_str = lambda x: f'"{x}"'
        scons_args = ' '.join([f"{key}={escape_str(option)}" for key, option in opitons.items()])
        save(self, os.path.join(self.source_folder, "scons_args"), scons_args)

    def build(self):
        with chdir(self, self.source_folder):
            options = load(self, "scons_args")
            self.run(f'scons build -j4 -Y "{self.source_folder}" {options}')

    def package(self):
        with chdir(self, self.source_folder):
            self.run(f'scons install -Y "{self.source_folder}"')
            rename(self, os.path.join(self.package_folder,"doc"), os.path.join(self.package_folder,"license"))
            rmdir(self, os.path.join(self.package_folder,"samples"))


    def package_info(self):
        self.cpp_info.libs = ["cantera_shared"] if self.options.shared else ["cantera"]
        self.cpp_info.resdirs = ["data"]

        if self.options.shared:
            self.cpp_info.libdirs = ["bin"] if self.settings.os == "Windows" else ["share"]
        else:
            self.cpp_info.libdirs = ["lib"]
