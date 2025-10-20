cmake_minimum_required(VERSION 3.20)

include(GNUInstallDirs)

if (UNIX AND NOT APPLE)
	set(LINUX TRUE)
endif()

option(BUILD_SHARED_LIBS "Build dynamic version of library" ON)

add_subdirectory(Dependencies/FreeType)
add_subdirectory(Dependencies/PicoPNG)

CPMAddPackage(
    NAME SDL3
    VERSION 3.2.24
    URL https://github.com/libsdl-org/SDL/releases/download/release-3.2.24/SDL3-devel-3.2.24-VC.zip
    DOWNLOAD_ONLY YES
)

if(SDL3_ADDED)
    set(SDL3_INCLUDE_DIR ${SDL3_SOURCE_DIR}/include)
    if(CMAKE_SIZEOF_VOID_P EQUAL 8)
        set(SDL3_LIBRARY_DIR ${SDL3_SOURCE_DIR}/lib/x64)
    else()
        set(SDL3_LIBRARY_DIR ${SDL3_SOURCE_DIR}/lib/x86)
    endif()
    
    add_library(SDL3::SDL3 SHARED IMPORTED)
    set_target_properties(SDL3::SDL3 PROPERTIES
        IMPORTED_LOCATION ${SDL3_LIBRARY_DIR}/SDL3.dll
        IMPORTED_IMPLIB ${SDL3_LIBRARY_DIR}/SDL3.lib
        INTERFACE_INCLUDE_DIRECTORIES ${SDL3_INCLUDE_DIR}
    )
endif()

CPMAddPackage(
    NAME imgui
    VERSION 1.92.4
    GITHUB_REPOSITORY ocornut/imgui
    GIT_TAG v1.92.4
    DOWNLOAD_ONLY YES
)

if(imgui_ADDED)
    set(IMGUI_SOURCES
        ${imgui_SOURCE_DIR}/imgui.cpp
        ${imgui_SOURCE_DIR}/imgui_demo.cpp
        ${imgui_SOURCE_DIR}/imgui_draw.cpp
        ${imgui_SOURCE_DIR}/imgui_tables.cpp
        ${imgui_SOURCE_DIR}/imgui_widgets.cpp
		${imgui_SOURCE_DIR}/backends/imgui_impl_sdl3.cpp
		${imgui_SOURCE_DIR}/backends/imgui_impl_opengl3.cpp
    )
    
    add_library(imgui STATIC ${IMGUI_SOURCES})
    target_include_directories(imgui PUBLIC ${imgui_SOURCE_DIR})
    
	target_include_directories(imgui PUBLIC ${imgui_SOURCE_DIR}/backends)
	target_link_libraries(imgui SDL3::SDL3)
	target_link_libraries(imgui ${OPENGL_gl_LIBRARY})
endif()

project(BearLibTerminal)

if(EXISTS "../CHANGELOG.md")
	file(STRINGS "../CHANGELOG.md" TERMINAL_VERSION_TOP_LINE LIMIT_COUNT 1)
	string(REGEX MATCH "[0-9\\.]+" TERMINAL_VERSION ${TERMINAL_VERSION_TOP_LINE})
else()
	set(TERMINAL_VERSION "Unknown")
endif()

# Detect system bitness
math(EXPR BITNESS "8*${CMAKE_SIZEOF_VOID_P}")

file(GLOB TERMINAL_HEADERS ./Source/*.hpp ./Source/*.h)
list(APPEND TERMINAL_HEADERS "${CMAKE_CURRENT_SOURCE_DIR}/Include/C/BearLibTerminal.h")
if(APPLE)
	file(GLOB TERMINAL_SOURCES ./Source/*.cpp ./Source/*.mm)
else()
	file(GLOB TERMINAL_SOURCES ./Source/*.cpp) # FIXME: manual selection
endif()

set(OpenGL_GL_PREFERENCE LEGACY)
find_package(OpenGL)
if (APPLE)
	find_library(COCOA_LIBRARY Cocoa)
endif()

include_directories(./Include/C)
include_directories(./Dependencies/FreeType/Include)
include_directories(./Dependencies/PicoPNG/Include)
include_directories(./Dependencies/NanoJPEG/Include)

add_library(BearLibTerminal ${TERMINAL_SOURCES} ${TERMINAL_HEADERS})
set_target_properties(BearLibTerminal PROPERTIES
	CXX_STANDARD 14
	CXX_STANDARD_REQUIRED TRUE)

target_compile_definitions(BearLibTerminal PRIVATE TERMINAL_VERSION=\"${TERMINAL_VERSION}\")

if(BUILD_SHARED_LIBS)
	if(NOT MSVC)
		target_link_libraries(BearLibTerminal -fvisibility=hidden)
	endif()
	if(MINGW)
		target_link_libraries(BearLibTerminal -static)
	elseif(LINUX)
		target_link_libraries(BearLibTerminal -static-libgcc)
	endif()
else()
	target_compile_definitions(BearLibTerminal PRIVATE BEARLIBTERMINAL_STATIC_BUILD)
endif()

target_link_libraries(BearLibTerminal freetype2 picopng ${OPENGL_gl_LIBRARY})
target_link_libraries(BearLibTerminal picopng)
target_link_libraries(BearLibTerminal ${OPENGL_gl_LIBRARY})
if(WIN32)
	target_compile_definitions(BearLibTerminal PRIVATE UNICODE)
	target_link_libraries(BearLibTerminal winmm.lib)
	target_link_libraries(BearLibTerminal ${PROJECT_SOURCE_DIR}/Resource/Terminal-${BITNESS}bit.res)
elseif(LINUX)
	target_link_libraries(BearLibTerminal pthread)
elseif(APPLE)
	target_link_libraries(BearLibTerminal ${COCOA_LIBRARY})
endif()

target_link_libraries(BearLibTerminal SDL3::SDL3)

target_link_libraries(BearLibTerminal imgui)

set(OUTPUT_DIR ${CMAKE_SOURCE_DIR}/Output/${CMAKE_SYSTEM_NAME}${BITNESS})
set_target_properties(BearLibTerminal PROPERTIES
	RUNTIME_OUTPUT_DIRECTORY ${OUTPUT_DIR}
	LIBRARY_OUTPUT_DIRECTORY ${OUTPUT_DIR}
	ARCHIVE_OUTPUT_DIRECTORY ${OUTPUT_DIR})

if (WIN32)
	# Fix unix-like "lib" prefix and ".a" suffix
	set_target_properties(BearLibTerminal PROPERTIES
		PREFIX ""
		SUFFIX ".dll"
		IMPORT_PREFIX ""
		IMPORT_SUFFIX ".lib")
	
	set(SDL3_DLL_SOURCE ${SDL3_LIBRARY_DIR}/SDL3.dll)
	set(SDL3_DLL_DEST $<TARGET_FILE_DIR:BearLibTerminal>/SDL3.dll)
	add_custom_command(TARGET BearLibTerminal POST_BUILD
		COMMAND ${CMAKE_COMMAND} -E copy_if_different
		${SDL3_DLL_SOURCE} ${SDL3_DLL_DEST}
		COMMENT "Copying SDL3.dll to executable directory"
	)
elseif (APPLE)
	set_target_properties(BearLibTerminal PROPERTIES
		BUILD_WITH_INSTALL_RPATH TRUE
		INSTALL_NAME_DIR "@executable_path")
endif()

install(TARGETS BearLibTerminal LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(FILES Include/C/BearLibTerminal.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
