#ifndef AUDIO_BRIDGE_H
#define AUDIO_BRIDGE_H

#include <cstdint>
#include <cstring>
#include <queue>
#include <mutex>
#include <thread>
#include <atomic>

constexpr int SAMPLE_RATE = 16000;
constexpr int CHANNELS = 1;
constexpr int BIT_DEPTH = 16;
constexpr int CHUNK_DURATION_MS = 500;
constexpr int CHUNK_SIZE = SAMPLE_RATE * CHANNELS * (BIT_DEPTH / 8) * CHUNK_DURATION_MS / 1000;

class AudioBridge {
public:
    AudioBridge();
    ~AudioBridge();
    
    bool init_capture();
    bool init_playback();
    void start();
    void stop();
    
    void set_websocket_enabled(bool enabled);
    void send_audio_chunk(const uint8_t* data, size_t size);
    
private:
    void capture_thread();
    void playback_thread();
    
    std::queue<std::vector<uint8_t>> capture_queue;
    std::queue<std::vector<uint8_t>> playback_queue;
    
    std::mutex capture_mutex;
    std::mutex playback_mutex;
    
    std::thread capture_thread_handle;
    std::thread playback_thread_handle;
    
    std::atomic<bool> running;
    std::atomic<bool> websocket_enabled;
    
    int capture_device;
    int playback_device;
};

#endif // AUDIO_BRIDGE_H
