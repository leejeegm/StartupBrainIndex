<?php
// 에러 출력 방지
error_reporting(0);
ini_set('display_errors', 0);

// 출력 버퍼 시작 (불필요한 출력 방지)
ob_start();

// CORS 헤더 추가 (필요한 경우)
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json; charset=utf-8');

// OPTIONS 요청 처리
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    ob_clean();
    http_response_code(200);
    ob_end_flush();
    exit;
}

try {
    // 현재 스크립트의 디렉토리 경로 사용
    $baseDir = __DIR__ . DIRECTORY_SEPARATOR;
    $pattern = $baseDir . 'uploads' . DIRECTORY_SEPARATOR . '*_metadata.json';
    $files = glob($pattern);
    $images = [];
    
    if ($files === false) {
        $files = [];
    }
    
    foreach ($files as $file) {
        if (!file_exists($file) || !is_readable($file)) {
            continue;
        }
        
        $fileContent = @file_get_contents($file);
        if ($fileContent === false) {
            continue;
        }
        
        $metadata = @json_decode($fileContent, true);
        
        if (!$metadata || !is_array($metadata)) {
            continue;
        }
        
        $imageId = $metadata['image_id'] ?? '';
        $filename = $metadata['filename'] ?? '';
        
        if (empty($imageId) || empty($filename)) {
            continue;
        }
        
        $imageFile = $baseDir . 'uploads' . DIRECTORY_SEPARATOR . $filename;
        
        if (!file_exists($imageFile)) {
            continue;
        }
        
        // 웹에서 접근 가능한 경로로 변환
        $webPath = 'uploads/' . $filename;
        
        $images[] = [
            'image_id' => $imageId,
            'filename' => $filename,
            'text' => $metadata['text'] ?? '',
            'description' => $metadata['description'] ?? '',
            'saved_at' => $metadata['saved_at'] ?? $metadata['created_at'] ?? '',
            'created_at' => $metadata['created_at'] ?? '',
            'image_url' => $webPath,
            'title' => $metadata['title'] ?? '',
            'tags' => $metadata['tags'] ?? []
        ];
    }
    
    // 저장일 기준으로 정렬 (최신순)
    usort($images, function($a, $b) {
        $dateA = $a['saved_at'] ?: $a['created_at'];
        $dateB = $b['saved_at'] ?: $b['created_at'];
        $timeA = $dateA ? strtotime($dateA) : 0;
        $timeB = $dateB ? strtotime($dateB) : 0;
        return $timeB - $timeA;
    });
    
    // 출력 버퍼 비우기
    ob_clean();
    
    echo json_encode([
        'success' => true,
        'images' => $images,
        'count' => count($images)
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    
} catch (Exception $e) {
    ob_clean();
    echo json_encode([
        'success' => false,
        'message' => '이미지 목록을 불러오는 중 오류가 발생했습니다: ' . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}

ob_end_flush();
?>
