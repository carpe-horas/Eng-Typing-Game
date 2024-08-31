let timeLeft = 40;  // 타이머를 40초로 설정
let timerId = null;

function startTimer() {
    if (!timerId) {  // 타이머가 이미 시작되지 않았다면 시작
        timerId = setInterval(() => {
            if (timeLeft <= 0) {
                clearInterval(timerId);
                alert('시간 초과!');
                document.getElementById('game-form').submit();  // 현재까지 입력된 내용 그대로 제출
            } else {
                timeLeft -= 1;  // 남은 시간 감소
                document.getElementById('time-left').textContent = timeLeft + '초'; // 남은 시간을 화면에 표시
            }
        }, 1000);
    }
}

// 타이머는 페이지가 로드될 때 자동으로 시작.
//document.addEventListener('DOMContentLoaded', startTimer);

function onInput() {
    startTimer();  // 타이핑 시작 시 타이머가 시작
}

function disableButton() {
    const submitButton = document.getElementById('submit-button');
    submitButton.disabled = true;
    submitButton.textContent = '로딩 중...';  
}

function endGame() {
    window.location.href = endGameUrl;  // 게임 종료 시 전달받은 URL로 이동
}

// 다른 언어 선택 버튼 클릭 이벤트
document.getElementById('change-language-button').onclick = function() {
    window.location.href = changeLanguageUrl;
};

// 게임 종료 버튼 클릭 이벤트
document.getElementById('end-game-button').onclick = endGame;
