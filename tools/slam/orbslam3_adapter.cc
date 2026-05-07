// =============================================
// orbslam3_adapter.cc
// 역할: ORB-SLAM3 라이브러리를 호출해 카메라 프레임 → pose/keyframe 점군 산출
//       후 stdout 으로 JSONL emit. backend 의 OrbSlam3Backend._read_stdout_loop 가 파싱.
//
// JSONL 메시지 형식:
//   {"type":"pose","x":..,"y":..,"z":..,"qw":..,"qx":..,"qy":..,"qz":..,"conf":..,"var":..}
//   {"type":"keyframe","frame":N,"points":[[x,y,z,r,g,b], ...]}
//
// 빌드: Dockerfile.orbslam3 의 g++ 단계 참조.
// 실행: ./orbslam3_adapter --vocab ... --calib ... --device /dev/video0 --mode mono
// =============================================
#include <iostream>
#include <iomanip>
#include <string>
#include <vector>
#include <opencv2/opencv.hpp>
#include <System.h>

namespace { // 작은 헬퍼들
std::string arg_value(int argc, char **argv, const std::string &flag, const std::string &dflt) {
    for (int i = 1; i + 1 < argc; ++i)
        if (flag == argv[i]) return argv[i + 1];
    return dflt;
}
inline void emit(const std::string &line) {
    std::cout << line << "\n";
    std::cout.flush();
}
} // anon

int main(int argc, char **argv) {
    const std::string vocab = arg_value(argc, argv, "--vocab", "/opt/orbslam3/vocabulary/ORBvoc.txt");
    const std::string calib = arg_value(argc, argv, "--calib", "/opt/orbslam3/config/skydroid_otg.yaml");
    const std::string device = arg_value(argc, argv, "--device", "/dev/video0");
    const std::string mode = arg_value(argc, argv, "--mode", "mono");

    auto sensor = (mode == "stereo") ? ORB_SLAM3::System::STEREO :
                   (mode == "rgbd") ? ORB_SLAM3::System::RGBD :
                                      ORB_SLAM3::System::MONOCULAR;
    ORB_SLAM3::System slam(vocab, calib, sensor, true /* viewer */);

    cv::VideoCapture cap(device, cv::CAP_V4L2);
    if (!cap.isOpened()) {
        std::cerr << "{\"type\":\"error\",\"msg\":\"cannot_open_device\"}\n";
        return 2;
    }
    int frame_idx = 0;
    cv::Mat frame;
    while (true) {
        if (!cap.read(frame)) break;
        const double ts = (double)cv::getTickCount() / cv::getTickFrequency();
        Sophus::SE3f Tcw = slam.TrackMonocular(frame, ts);
        ++frame_idx;

        // pose
        Eigen::Quaternionf q(Tcw.rotationMatrix());
        Eigen::Vector3f t = Tcw.translation();
        std::ostringstream ps;
        ps << std::fixed << std::setprecision(5)
           << "{\"type\":\"pose\",\"x\":" << t.x()
           << ",\"y\":" << t.y() << ",\"z\":" << t.z()
           << ",\"qw\":" << q.w() << ",\"qx\":" << q.x()
           << ",\"qy\":" << q.y() << ",\"qz\":" << q.z()
           << ",\"conf\":" << (slam.GetTrackingState() == 2 ? 0.85 : 0.2)
           << ",\"var\":" << 0.05 << "}";
        emit(ps.str());

        // keyframe (5 프레임마다 — 부하 통제)
        if (frame_idx % 5 == 0) {
            const auto keyframes = slam.GetAllKeyframes();
            std::ostringstream kf;
            kf << "{\"type\":\"keyframe\",\"frame\":" << frame_idx << ",\"points\":[";
            bool first = true;
            for (auto *pMP : slam.GetTrackedMapPoints()) {
                if (!pMP || pMP->isBad()) continue;
                Eigen::Vector3f wp = pMP->GetWorldPos();
                if (!first) kf << ",";
                kf << "[" << wp.x() << "," << wp.y() << "," << wp.z()
                   // ORB-SLAM3 기본은 색상 정보 없음 — 원본 영상에서 patch RGB 평균을 추출하는 보강은 후속.
                   << ",180,180,180]";
                first = false;
            }
            kf << "]}";
            emit(kf.str());
        }
    }
    slam.Shutdown();
    return 0;
}
