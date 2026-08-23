// folder_scanner.cpp
//
// Native folder-size walker for Windows, exposed to Python via ctypes.
// Build (from a MinGW64 shell):
//     g++ -O3 -shared -o folder_scanner.dll folder_scanner.cpp ^
//         -static -static-libgcc -static-libstdc++
//
// This produces folder_scanner.dll next to your Python script.

#include <windows.h>
#include <string>
#include <cstdint>

extern "C" {

// Returns true if the given attributes mark a reparse point
// (symlink OR NTFS junction/mount point - both must be skipped
// to avoid infinite loops / double-counting, same issue that
// bit the Python version).
static inline bool is_reparse_point(DWORD attrs) {
    return (attrs & FILE_ATTRIBUTE_REPARSE_POINT) != 0;
}

// Recursively sums file sizes under `path`. Skips reparse points,
// skips anything it can't access (permission errors), same
// semantics as the Python version's try/except (PermissionError, OSError).
static uint64_t scan_dir(const std::wstring& path) {
    uint64_t total = 0;

    std::wstring pattern = path;
    if (!pattern.empty() && pattern.back() != L'\\') {
        pattern += L'\\';
    }
    pattern += L'*';

    WIN32_FIND_DATAW findData;
    HANDLE hFind = FindFirstFileW(pattern.c_str(), &findData);

    if (hFind == INVALID_HANDLE_VALUE) {
        // Can't open this directory (permissions, etc.) - skip it,
        // matching the Python except (PermissionError, OSError): pass
        return 0;
    }

    do {
        const wchar_t* name = findData.cFileName;

        // Skip "." and ".."
        if (name[0] == L'.' &&
            (name[1] == L'\0' || (name[1] == L'.' && name[2] == L'\0'))) {
            continue;
        }

        if (is_reparse_point(findData.dwFileAttributes)) {
            continue;
        }

        std::wstring fullPath = path;
        if (!fullPath.empty() && fullPath.back() != L'\\') {
            fullPath += L'\\';
        }
        fullPath += name;

        if (findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
            total += scan_dir(fullPath);
        } else {
            LARGE_INTEGER size;
            size.HighPart = findData.nFileSizeHigh;
            size.LowPart = findData.nFileSizeLow;
            total += static_cast<uint64_t>(size.QuadPart);
        }
    } while (FindNextFileW(hFind, &findData));

    FindClose(hFind);
    return total;
}

// Exported entry point. Takes a UTF-16 (wchar_t*) path, as Python's
// ctypes.c_wchar_p maps directly to this on Windows.
__declspec(dllexport) unsigned long long get_folder_size(const wchar_t* path) {
    if (path == nullptr) return 0;
    return static_cast<unsigned long long>(scan_dir(std::wstring(path)));
}

} // extern "C"