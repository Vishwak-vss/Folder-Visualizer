#pragma once
#include <string>
#include <vector>
#include <filesystem>
#include <atomic>
#include <future>
#include <nlohmann/json.hpp>

namespace fs = std::filesystem;
using json = nlohmann::json;

class FastScanner {
public:
    std::atomic<bool> cancelToken{false};

    json scanDirectory(const std::string& pathStr, uint64_t smallThreshold = 51200) {
        cancelToken = false;
        fs::path targetPath(pathStr);
        return scanRecursive(targetPath, smallThreshold);
    }

private:
    json scanRecursive(const fs::path& dirPath, uint64_t smallThreshold) {
        json node;
        node["name"] = dirPath.filename().string().empty() ? dirPath.string() : dirPath.filename().string();
        node["path"] = dirPath.string();

        if (cancelToken.load()) return node;

        uint64_t totalSize = 0;
        uint64_t accumulatedSmallSize = 0;
        json children = json::array();

        try {
            if (fs::exists(dirPath) && fs::is_directory(dirPath)) {
                for (const auto& entry : fs::directory_iterator(dirPath, fs::directory_options::skip_permission_denied)) {
                    if (cancelToken.load()) break;

                    try {
                        if (fs::is_directory(entry.status())) {
                            json child = scanRecursive(entry.path(), smallThreshold);
                            uint64_t childSize = child.value("size", 0ULL);
                            if (childSize >= smallThreshold) {
                                totalSize += childSize;
                                children.push_back(child);
                            } else if (childSize > 0) {
                                accumulatedSmallSize += childSize;
                                totalSize += childSize;
                            }
                        } else if (fs::is_regular_file(entry.status())) {
                            uint64_t fileSize = fs::file_size(entry.path());
                            if (fileSize >= smallThreshold) {
                                totalSize += fileSize;
                                json fileNode;
                                fileNode["name"] = entry.path().filename().string();
                                fileNode["path"] = entry.path().string();
                                fileNode["size"] = fileSize;
                                fileNode["isFile"] = true;
                                children.push_back(fileNode);
                            } else if (fileSize > 0) {
                                accumulatedSmallSize += fileSize;
                                totalSize += fileSize;
                            }
                        }
                    } catch (...) {}
                }
            }
        } catch (...) {}

        if (accumulatedSmallSize > 0) {
            json othersNode;
            othersNode["name"] = "Others (< 50 KB)";
            othersNode["path"] = dirPath.string();
            othersNode["size"] = accumulatedSmallSize;
            othersNode["isOthers"] = true;
            children.push_back(othersNode);
        }

        node["size"] = totalSize;
        node["children"] = children;
        return node;
    }
};