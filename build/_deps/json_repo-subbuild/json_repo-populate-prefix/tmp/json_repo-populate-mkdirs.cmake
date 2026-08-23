# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file LICENSE.rst or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION ${CMAKE_VERSION}) # this file comes with cmake

# If CMAKE_DISABLE_SOURCE_CHANGES is set to true and the source directory is an
# existing directory in our source tree, calling file(MAKE_DIRECTORY) on it
# would cause a fatal error, even though it would be a no-op.
if(NOT EXISTS "C:/Users/Vishwak/Desktop/Projects/file-percentage-viewer/build/_deps/json_repo-src")
  file(MAKE_DIRECTORY "C:/Users/Vishwak/Desktop/Projects/file-percentage-viewer/build/_deps/json_repo-src")
endif()
file(MAKE_DIRECTORY
  "C:/Users/Vishwak/Desktop/Projects/file-percentage-viewer/build/_deps/json_repo-build"
  "C:/Users/Vishwak/Desktop/Projects/file-percentage-viewer/build/_deps/json_repo-subbuild/json_repo-populate-prefix"
  "C:/Users/Vishwak/Desktop/Projects/file-percentage-viewer/build/_deps/json_repo-subbuild/json_repo-populate-prefix/tmp"
  "C:/Users/Vishwak/Desktop/Projects/file-percentage-viewer/build/_deps/json_repo-subbuild/json_repo-populate-prefix/src/json_repo-populate-stamp"
  "C:/Users/Vishwak/Desktop/Projects/file-percentage-viewer/build/_deps/json_repo-subbuild/json_repo-populate-prefix/src"
  "C:/Users/Vishwak/Desktop/Projects/file-percentage-viewer/build/_deps/json_repo-subbuild/json_repo-populate-prefix/src/json_repo-populate-stamp"
)

set(configSubDirs Debug)
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "C:/Users/Vishwak/Desktop/Projects/file-percentage-viewer/build/_deps/json_repo-subbuild/json_repo-populate-prefix/src/json_repo-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "C:/Users/Vishwak/Desktop/Projects/file-percentage-viewer/build/_deps/json_repo-subbuild/json_repo-populate-prefix/src/json_repo-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
