cmake_minimum_required(VERSION 3.20)
project(TombiEUResidentAudit LANGUAGES C CXX)
get_filename_component(TOMBA_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
set(PSXRECOMP_ROOT "${TOMBA_ROOT}/psxrecomp")
set(eu_catalog "${TOMBA_ROOT}/build-eu-seamless/generated/eu_catalog.inc")
if(NOT EXISTS "${eu_catalog}")
    message(FATAL_ERROR "Run python -I eu/seamless_catalog.py first")
endif()
add_executable(tombi-resident-tests
    "${TOMBA_ROOT}/tests/test_seamless_prepare.cpp"
    "${TOMBA_ROOT}/src/mods/tomba_seamless_prepare.cpp"
    "${PSXRECOMP_ROOT}/runtime/src/mod_resident.cpp"
    "${PSXRECOMP_ROOT}/runtime/src/psx_sha256.c")
target_include_directories(tombi-resident-tests PRIVATE
    "${TOMBA_ROOT}/src/mods" "${PSXRECOMP_ROOT}/runtime/include")
target_compile_features(tombi-resident-tests PRIVATE cxx_std_17)
target_compile_definitions(tombi-resident-tests PRIVATE
    TOMBA_SEAMLESS_CATALOG_HEADER="${eu_catalog}"
    TOMBA_SEAMLESS_PACK_FORMAT="sces01330-rev1-five-languages-gam-v1")
add_executable(tomba-us-resident-tests
    "${TOMBA_ROOT}/tests/test_seamless_prepare.cpp"
    "${TOMBA_ROOT}/src/mods/tomba_seamless_prepare.cpp"
    "${PSXRECOMP_ROOT}/runtime/src/mod_resident.cpp"
    "${PSXRECOMP_ROOT}/runtime/src/psx_sha256.c")
target_include_directories(tomba-us-resident-tests PRIVATE
    "${TOMBA_ROOT}/src/mods" "${PSXRECOMP_ROOT}/runtime/include")
target_compile_features(tomba-us-resident-tests PRIVATE cxx_std_17)
