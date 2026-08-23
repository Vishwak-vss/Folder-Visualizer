#include <windows.h>
#include <wrl.h>
#include <wil/com.h>
#include <WebView2.h>
#include <shlobj.h>
#include <iostream>
#include <thread>
#include <vector>
#include "scanner.h"

using namespace Microsoft::WRL;

HWND g_hWnd;
wil::com_ptr<ICoreWebView2Controller> g_controller;
wil::com_ptr<ICoreWebView2> g_webview;
FastScanner g_scanner;

void EnableDPIAwareness() {
    HMODULE hUser32 = GetModuleHandleW(L"user32.dll");
    if (hUser32) {
        typedef BOOL(WINAPI* SetProcessDpiAwarenessContextProc)(DPI_AWARENESS_CONTEXT);
        SetProcessDpiAwarenessContextProc setDpi = 
            (SetProcessDpiAwarenessContextProc)GetProcAddress(hUser32, "SetProcessDpiAwarenessContext");
        if (setDpi) {
            setDpi(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
        }
    }
}

std::vector<std::string> GetSystemDrives() {
    std::vector<std::string> drives;
    DWORD mask = GetLogicalDrives();
    for (char i = 0; i < 26; ++i) {
        if (mask & (1 << i)) {
            std::string drive = "";
            drive += (char)('A' + i);
            drive += ":\\";
            drives.push_back(drive);
        }
    }
    return drives;
}

std::string PickFolder() {
    std::string folderPath = "";
    wil::com_ptr<IFileDialog> pfd;
    if (SUCCEEDED(CoCreateInstance(CLSID_FileOpenDialog, NULL, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&pfd)))) {
        DWORD dwOptions;
        if (SUCCEEDED(pfd->GetOptions(&dwOptions))) {
            pfd->SetOptions(dwOptions | FOS_PICKFOLDERS);
        }
        if (SUCCEEDED(pfd->Show(g_hWnd))) {
            wil::com_ptr<IShellItem> psi;
            if (SUCCEEDED(pfd->GetResult(&psi))) {
                PWSTR pszPath = nullptr;
                if (SUCCEEDED(psi->GetDisplayName(SIGDN_FILESYSPATH, &pszPath))) {
                    std::wstring wstr(pszPath);
                    folderPath = std::string(wstr.begin(), wstr.end());
                    CoTaskMemFree(pszPath);
                }
            }
        }
    }
    return folderPath;
}

void StartAsyncScan(std::string targetPath) {
    g_scanner.cancelToken = true;
    
    std::thread([targetPath]() {
        json result = g_scanner.scanDirectory(targetPath);
        
        json response;
        response["type"] = "scanResult";
        response["payload"] = result;
        std::string jsonStr = response.dump();

        if (g_webview) {
            std::wstring wstr(jsonStr.begin(), jsonStr.end());
            g_webview->PostWebMessageAsJson(wstr.c_str());
        }
    }).detach();
}

void SendInitialData() {
    json response;
    response["type"] = "initData";
    response["drives"] = GetSystemDrives();
    std::string jsonStr = response.dump();

    if (g_webview) {
        std::wstring wstr(jsonStr.begin(), jsonStr.end());
        g_webview->PostWebMessageAsJson(wstr.c_str());
    }
}

LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    case WM_SIZE:
        if (g_controller) {
            RECT bounds;
            GetClientRect(hWnd, &bounds);
            g_controller->put_Bounds(bounds);
        }
        break;
    case WM_DPICHANGED: {
        RECT* const prcNewWindow = (RECT*)lParam;
        SetWindowPos(hWnd, NULL, prcNewWindow->left, prcNewWindow->top,
            prcNewWindow->right - prcNewWindow->left, prcNewWindow->bottom - prcNewWindow->top,
            SWP_NOZORDER | SWP_NOACTIVATE);
        break;
    }
    case WM_DESTROY:
        PostQuitMessage(0);
        break;
    default:
        return DefWindowProc(hWnd, message, wParam, lParam);
    }
    return 0;
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    EnableDPIAwareness();

    WNDCLASSEXW wcex = { sizeof(WNDCLASSEX) };
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = WndProc;
    wcex.hInstance = hInstance;
    wcex.hCursor = LoadCursor(NULL, IDC_ARROW);
    wcex.lpszClassName = L"StorageVisualizerClass";
    RegisterClassExW(&wcex);

    g_hWnd = CreateWindowW(L"StorageVisualizerClass", L"Storage Visualizer", WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 1080, 780, NULL, NULL, hInstance, NULL);

    ShowWindow(g_hWnd, nCmdShow);
    UpdateWindow(g_hWnd);

    CreateCoreWebView2EnvironmentWithOptions(nullptr, nullptr, nullptr,
        Callback<ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler>(
            [hInstance](HRESULT result, ICoreWebView2Environment* env) -> HRESULT {
                if (!env) return S_OK;
                env->CreateCoreWebView2Controller(g_hWnd,
                    Callback<ICoreWebView2CreateCoreWebView2ControllerCompletedHandler>(
                        [](HRESULT result, ICoreWebView2Controller* controller) -> HRESULT {
                            if (controller) {
                                g_controller = controller;
                                g_controller->get_CoreWebView2(&g_webview);

                                RECT bounds;
                                GetClientRect(g_hWnd, &bounds);
                                g_controller->put_Bounds(bounds);

                                g_webview->add_WebMessageReceived(
                                    Callback<ICoreWebView2WebMessageReceivedEventHandler>(
                                        [](ICoreWebView2* sender, ICoreWebView2WebMessageReceivedEventArgs* args) -> HRESULT {
                                            LPWSTR jsonRaw = nullptr;
                                            if (SUCCEEDED(args->TryGetWebMessageAsString(&jsonRaw)) && jsonRaw) {
                                                std::wstring wstr(jsonRaw);
                                                std::string str(wstr.begin(), wstr.end());
                                                json msg = json::parse(str);
                                                
                                                if (msg.contains("command")) {
                                                    if (msg["command"] == "scan") {
                                                        StartAsyncScan(msg["path"]);
                                                    } else if (msg["command"] == "browseFolder") {
                                                        std::string chosenPath = PickFolder();
                                                        if (!chosenPath.empty()) {
                                                            StartAsyncScan(chosenPath);
                                                        }
                                                    }
                                                }
                                                CoTaskMemFree(jsonRaw);
                                            }
                                            return S_OK;
                                        }).Get(), nullptr);

                                char exePath[MAX_PATH];
                                GetModuleFileNameA(NULL, exePath, MAX_PATH);
                                std::string dir(exePath);
                                std::string htmlPath = "file:///" + dir.substr(0, dir.find_last_of("\\/")) + "/web/index.html";
                                std::wstring wHtmlPath(htmlPath.begin(), htmlPath.end());
                                
                                g_webview->Navigate(wHtmlPath.c_str());
                            }
                            return S_OK;
                        }).Get());
                return S_OK;
            }).Get());

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    CoUninitialize();
    return (int)msg.wParam;
}