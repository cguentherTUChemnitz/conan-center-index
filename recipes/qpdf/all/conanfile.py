from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.microsoft import is_msvc_static_runtime, is_msvc
from conan.tools.files import get, copy, rm, rmdir
from conan.tools.build import check_min_cppstd
from conan.tools.scm import Version
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
import os

required_conan_version = ">=1.51.3"

class PackageConan(ConanFile):
    name = "qpdf"
    description = "QPDF is a command-line tool and C++ library that performs content-preserving transformations on PDF files."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/qpdf/qpdf"
    topics = ("pdf")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _minimum_cpp_standard(self):
        return 14

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "5",
            "Visual Studio": "19.10",
            "clang": "3.4",
            "apple-clang": "10",
        }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            try:
                del self.options.fPIC # once removed by config_options, need try..except for a second del
            except Exception:
                pass

    def layout(self):
        cmake_layout(self, src_folder="src") # src_folder must use the same source folder name the project

    def requirements(self):
        # https://qpdf.readthedocs.io/en/stable/installation.html#basic-dependencies
        self.requires("zlib/1.2.12")
        self.requires("libjpeg-turbo/2.1.4")


    def validate(self):
        # validate the minimum cpp standard supported. For C++ projects only
        if self.info.settings.compiler.cppstd:
            check_min_cppstd(self, self._minimum_cpp_standard)
        minimum_version = self._compilers_minimum_version.get(str(self.info.settings.compiler), False)
        if minimum_version and Version(self.info.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(f"{self.ref} requires C++{self._minimum_cpp_standard}, which your compiler does not support.")

    def build_requirements(self):
        self.tool_requires("cmake/3.24.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
                  destination=self.source_folder, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["BUILD_STATIC_LIBS"] = not self.options.shared
        tc.variables["USE_IMPLICIT_CRYPTO"] = False
        tc.variables["REQUIRE_CRYPTO_NATIVE"] = True
        tc.variables["REQUIRE_CRYPTO_GNUTLS"] = False
        tc.variables["REQUIRE_CRYPTO_OPENSSL"] = False
        tc.generate()
        # In case there are dependencies listed on requirements, CMakeDeps should be used
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

        # some files extensions and folders are not allowed. Please, read the FAQs to get informed.
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.la",  os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.libs = ["qpdf"]
        # if package provides a CMake config file (package-config.cmake or packageConfig.cmake, with package::package target, usually installed in <prefix>/lib/cmake/<package>/)
        self.cpp_info.set_property("cmake_file_name", "QPDF")
        self.cpp_info.set_property("cmake_target_name", "qpdf::libqpdf")
        # if package provides a pkgconfig file (package.pc, usually installed in <prefix>/lib/pkgconfig/)
        self.cpp_info.set_property("pkg_config_name", "libqpdf")

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "QPDF"
        self.cpp_info.filenames["cmake_find_package_multi"] = "QPDF"
        self.cpp_info.names["cmake_find_package"] = "QPDF"
        self.cpp_info.names["cmake_find_package_multi"] = "QPDF"
