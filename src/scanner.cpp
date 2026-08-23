#include <windows.h>
#include <wrl.h>
#include <wil/com.h>
#include <WebView2.h>
#include <shlobj.h>
#include <iostream>
#include <thread>
#include "scanner.h"

using namespace Microsoft::WRL;

HWND g_hWnd;
wil::com_ptr<ICoreWebView2Controller> g_controller;
wil::com_ptr<ICoreWebView2> g_webview;
FastScanner g_scanner;

std::string GetHomeDirectory() {
    char path[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_PROFILE, NULL, 0, path))) {
        return std::string(path);
    }
    return "C:\\";
}

void StartAsyncScan(std::string targetPath) {
    g_scanner.cancelToken = true; // Interrupt active scan
    
    std::thread([targetPath]() {
        json result = g_scanner.scanDirectory(targetPath);
        
        json response;
        response["type"] = "scanResult";
        response["payload"] = result;
        std::string jsonStr = response.dump();

        // Post JSON back to JS UI thread
        PostTask(g_hWnd, [jsonStr]() {
            if (g_webview) {
                std::wstring wstr(jsonStr.begin(), jsonStr.end());
                g_webview->PostWebMessageAsJson(wstr.c_str());
            }
        });
    }).detach();
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
    case WM_DESTROY:
        PostQuitMessage(0);
        break;
    default:
        return DefWindowProc(hWnd, message, wParam, lParam);
    }
    return 0;
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    WNDCLASSEXW wcex = { sizeof(WNDCLASSEX) };
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = WndProc;
    wcex.hInstance = hInstance;
    wcex.hCursor = LoadCursor(NULL, IDC_ARROW);
    wcex.lpszClassName = L"StorageVisualizerClass";
    RegisterClassExW(&wcex);

    g_hWnd = CreateWindowW(L"StorageVisualizerClass", L"Storage Visualizer", WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 960, 720, NULL, NULL, hInstance, NULL);

    ShowWindow(g_hWnd, nCmdShow);
    UpdateWindow(g_hWnd);

    // Initialize WebView2
    CreateCoreWebView2EnvironmentWithOptions(sub, sub, nullptr,
        Callback<ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler>(
            [hInstance](HRESULT result, ICoreWebView2Environment* env) -> HRESULT {
                env->CreateCoreWebView2Controller(g_hWnd,
                    Callback<ICoreWebView2CreateCoreWebView2ControllerCompletedHandler>(
                        [](HRESULT result, ICoreWebView2Controller* controller) -> HRESULT {
                            if (controller) {
                                g_controller = controller;
                                g_controller->get_CoreWebView2(&g_webview);

                                RECT bounds;
                                GetClientRect(g_hWnd, &bounds);
                                g_controller->put_Bounds(bounds);

                                // Register JS -> C++ Bridge
                                g_webview->add_WebMessageReceived(
                                    Callback<ICoreWebView2WebMessageReceivedEventHandler>(
                                        [](ICoreWebView2* sender, ICoreWebView2WebMessageReceivedEventArgs* args) -> HRESULT {
                                            LPWSTR jsonRaw;
                                            args->get_WebMessageAsString(&jsonRaw);
                                            json msg = json::parse(jsonRaw);
                                            
                                            if (msg["command"] == "scan") {
                                                StartAsyncScan(msg["path"]);
                                            }
                                            return S_OK;
                                        }).Get(), nullptr);

                                // Navigate to index.html
                                char exePath[MAX_PATH];
                                GetModuleFileNameA(NULL, exePath, MAX_PATH);
                                std::string dir(exePath);
                                std::string htmlPath = "file:///" + dir.substr(0, dir.find_last_of("\\/")) + "/web/index.html";
                                std::wstring wHtmlPath(htmlPath.begin(), htmlPath.end());
                                
                                g_webview->Navigate(wHtmlPath.c_str());

                                // Initial Auto Scan (User Home Folder)
                                StartAsyncScan(GetHomeDirectory());
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
    return (int)msg.wParam;
}