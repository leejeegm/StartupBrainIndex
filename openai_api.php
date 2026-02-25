<?php
/**
 * OpenAI API 호출을 위한 별도 파일
 * curl 명령어를 사용하여 호출
 */

function callOpenAIAPI($endpoint, $data, $apiKey) {
    $url = "https://api.openai.com/v1/" . $endpoint;
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $apiKey
    ]);
    curl_setopt($ch, CURLOPT_TIMEOUT, 120); // 타임아웃 120초
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 30); // 연결 타임아웃 30초
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        return ['error' => true, 'message' => 'CURL Error: ' . $error, 'http_code' => $httpCode];
    }
    
    if ($httpCode !== 200) {
        $errorData = @json_decode($response, true);
        $errorMessage = 'HTTP Error: ' . $httpCode;
        if ($errorData && isset($errorData['error']['message'])) {
            $errorMessage .= ' - ' . $errorData['error']['message'];
        } else {
            $errorMessage .= ' - ' . substr($response, 0, 200);
        }
        return ['error' => true, 'message' => $errorMessage, 'http_code' => $httpCode, 'response' => $response];
    }
    
    $decoded = json_decode($response, true);
    if ($decoded === null) {
        return ['error' => true, 'message' => 'JSON 디코딩 실패: ' . json_last_error_msg()];
    }
    
    return ['error' => false, 'data' => $decoded];
}

function generateImageWithDALLE($prompt, $apiKey) {
    $data = [
        'model' => 'dall-e-3',
        'prompt' => $prompt,
        'n' => 1,
        'size' => '1024x1024',
        'quality' => 'standard'
    ];
    
    return callOpenAIAPI('images/generations', $data, $apiKey);
}

function getImageDescription($imageBase64, $apiKey) {
    $data = [
        'model' => 'gpt-4o',
        'messages' => [
            [
                'role' => 'user',
                'content' => [
                    [
                        'type' => 'text',
                        'text' => '이 이미지를 자세히 분석하고 설명해주세요. 이미지의 내용, 색상, 구성, 분위기 등을 포함하여 상세하게 설명해주세요.'
                    ],
                    [
                        'type' => 'image_url',
                        'image_url' => [
                            'url' => 'data:image/jpeg;base64,' . $imageBase64
                        ]
                    ]
                ]
            ]
        ],
        'max_tokens' => 1000
    ];
    
    return callOpenAIAPI('chat/completions', $data, $apiKey);
}

function analyzeTextFile($textContent, $apiKey) {
    $data = [
        'model' => 'gpt-4o',
        'messages' => [
            [
                'role' => 'user',
                'content' => '다음 텍스트 내용을 분석하고, 이를 이미지로 표현할 수 있는 상세한 프롬프트를 작성해주세요. 이미지 생성에 적합한 구체적이고 자세한 설명을 제공해주세요: ' . $textContent
            ]
        ],
        'max_tokens' => 500
    ];
    
    return callOpenAIAPI('chat/completions', $data, $apiKey);
}

function suggestImageTitles($text, $description, $apiKey) {
    $prompt = "다음 텍스트와 이미지 설명을 바탕으로 이미지에 어울리는 제목을 3개 추천해주세요.\n\n";
    $prompt .= "원본 텍스트: " . $text . "\n\n";
    $prompt .= "이미지 설명: " . $description . "\n\n";
    $prompt .= "제목은 각 줄에 하나씩, 번호 없이 제목만 작성해주세요. 예시:\n";
    $prompt .= "제목1\n제목2\n제목3";
    
    $data = [
        'model' => 'gpt-4o',
        'messages' => [
            [
                'role' => 'user',
                'content' => $prompt
            ]
        ],
        'max_tokens' => 200
    ];
    
    return callOpenAIAPI('chat/completions', $data, $apiKey);
}
?>
