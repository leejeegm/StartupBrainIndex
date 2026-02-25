<?php
error_reporting(0);
ini_set('display_errors', 0);
ob_start();

header('Content-Type: application/json; charset=utf-8');

try {
    $input = json_decode(file_get_contents('php://input'), true);
    $keyword = $input['keyword'] ?? '';

    if (empty($keyword)) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '검색 키워드를 입력해주세요.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

    $results = [];
    $pattern = 'uploads/*_metadata.json';
    $files = glob($pattern);
    
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
        
        $text = $metadata['text'] ?? '';
        $description = $metadata['description'] ?? '';
        $filename = $metadata['filename'] ?? '';
        
        // 키워드 검색 (텍스트, 설명, 파일명에서 검색)
        if (stripos($text, $keyword) !== false || 
            stripos($description, $keyword) !== false || 
            stripos($filename, $keyword) !== false) {
            
            $imageId = $metadata['image_id'] ?? '';
            $imageFile = 'uploads/' . $metadata['filename'];
            
            if (file_exists($imageFile)) {
                $results[] = [
                    'image_id' => $imageId,
                    'filename' => $filename,
                    'text' => $text,
                    'description' => $description,
                    'saved_at' => $metadata['saved_at'] ?? $metadata['created_at'] ?? '',
                    'image_url' => $imageFile
                ];
            }
        }
    }

    // 저장일 기준으로 정렬 (최신순)
    usort($results, function($a, $b) {
        $timeA = $a['saved_at'] ? strtotime($a['saved_at']) : 0;
        $timeB = $b['saved_at'] ? strtotime($b['saved_at']) : 0;
        return $timeB - $timeA;
    });

    ob_clean();
    echo json_encode([
        'success' => true,
        'results' => $results,
        'count' => count($results)
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    
} catch (Exception $e) {
    ob_clean();
    echo json_encode([
        'success' => false,
        'message' => '검색 중 오류가 발생했습니다: ' . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}

ob_end_flush();
?>
