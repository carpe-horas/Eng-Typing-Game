from flask import Flask, render_template, request, redirect, url_for, session
import json
from googletrans import Translator
import time, random
from collections import Counter

app = Flask(__name__)
app.secret_key = 'my_secret_key'

# JSON 파일에서 인용구 로드
def load_quotes():
    with open('quotes.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 인용구 데이터 초기화
all_quotes = load_quotes()
all_quotes.sort(key=lambda x: len(x['quote']))  # 인용구를 길이 순으로 정렬
quotes = {i: all_quotes[(i-1)*10:i*10] for i in range(1, 11)}

# 점수와 통계 초기화
score = 0
level = 1
level_sentences_used = []
mistake_counter = Counter()
total_time_taken = 0
total_cpm = 0
total_errors = 0
total_attempts = 0

# 번역 함수 정의
def translate_text(text, target_lang='ko'):
    try:
        translator = Translator()
        translation = translator.translate(text, dest=target_lang)
        return translation.text
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text  # 번역 실패 시 원문을 반환

# get_translated_quote 함수 정의
def get_translated_quote(quote, author, language):
    if language == 'ko':
        return quote, author  # 이미 번역된 텍스트 사용
    if language != 'en':  # 영어가 아닌 경우에만 번역
        translated_quote = translate_text(quote, target_lang=language)
        translated_author = translate_text(author, target_lang=language)
    else:
        translated_quote = quote
        translated_author = author
    return translated_quote, translated_author

# get_next_quote 함수 정의
def get_next_quote(language):
    global level_sentences_used, level
    if len(level_sentences_used) == 0:
        if level <= 10 and len(quotes[level]) > 0:
            available_sentences = len(quotes[level])
            sample_size = min(4, available_sentences)  # 남은 문장의 수와 4 중 작은 값으로 샘플링
            level_sentences_used = random.sample(quotes[level], sample_size)
        else:
            return None, None, None  # 더 이상 문장이 없을 경우 None 반환

    selected_quote = level_sentences_used.pop(0)
    
    # 한국어를 선택한 경우 미리 번역된 문장 사용
    if language == 'ko':
        return selected_quote["translation"], selected_quote["author"], selected_quote["translation"]
    else:
        translated_quote, translated_author = get_translated_quote(selected_quote["quote"], selected_quote["author"], language)
        return translated_quote, translated_author, selected_quote["translation"]


def calculate_results(user_input, selected_sentence, elapsed_time):
    global mistake_counter, total_errors, total_cpm, total_attempts

    # 오타 계산 및 실수한 단어 기록
    input_words = user_input.split()
    sentence_words = selected_sentence.split()

    errors = 0

    # 모든 단어를 비교하여 실수 처리
    for i, word in enumerate(sentence_words):
        if i < len(input_words):
            if word != input_words[i]:
                errors += 1
                mistake_counter[word] += 1
        else:
            # 입력하지 않은 단어를 실수로 처리
            errors += 1
            mistake_counter[word] += 1

    # 입력된 단어 중 남은 부분이 있으면 모두 실수로 처리
    if len(input_words) > len(sentence_words):
        errors += len(input_words) - len(sentence_words)
        for word in input_words[len(sentence_words):]:
            mistake_counter[word] += 1

    total_errors += errors

    # 정확도 계산
    accuracy = (len(sentence_words) - errors) / len(sentence_words) * 100 if len(sentence_words) > 0 else 0

    # 1분당 타자 수 (CPM) 계산
    cpm = (len(user_input) / elapsed_time) * 60 if elapsed_time > 0 else 0
    total_cpm += cpm

    # 점수 계산
    base_score = (len(selected_sentence) / 5) * (accuracy / 100)
    time_bonus = max(0, (40 - elapsed_time)) * (accuracy / 100)  # 40초 기준에서 남은 시간 보너스
    round_score = int(base_score + time_bonus)

    # **보너스 점수 계산**
    # 문장이 완전히 일치하는 경우
    if user_input == selected_sentence:
        round_score += 50  # 예: 완전히 일치 시 50점 보너스

    # 정확도 100%인 경우
    if accuracy == 100:
        round_score += 25  # 예: 정확도 100% 시 25점 보너스

    # **남은 시간 보너스**
    remaining_time = max(0, 40 - elapsed_time)  # 남은 시간 계산
    time_bonus = int(remaining_time * 2)  # 예: 남은 1초당 2점 보너스
    round_score += time_bonus

    total_attempts += 1

    results = {
        'time_taken': round(elapsed_time, 2),
        'cpm': round(cpm, 2),
        'errors': errors,
        'accuracy': round(accuracy, 2),
        'score': round(round_score)
    }

    return results


# 첫 화면: 언어 선택
@app.route('/', methods=['GET', 'POST'])
def choose_language():
    if request.method == 'POST':
        language = request.form.get('language')
        session['language'] = language
        return redirect(url_for('index'))
    return render_template('choose_language.html')

# 타이핑 게임 화면
@app.route('/game', methods=['GET', 'POST'])
def index():
    if 'language' not in session:
        return redirect(url_for('choose_language'))

    language = session.get('language', 'en')
    global score, level, level_sentences_used, total_time_taken, total_cpm, total_errors, total_attempts, mistake_counter

    if request.method == 'GET':
        score = 0
        level = 1
        level_sentences_used.clear()
        total_time_taken = 0
        total_cpm = 0
        total_errors = 0
        total_attempts = 0
        mistake_counter.clear()

        # 여기서 get_next_quote에 language를 전달합니다.
        selected_quote, author, translation = get_next_quote(language)
        
        if language == 'ko':
            selected_quote = translation
        else:
            selected_quote, author = get_translated_quote(selected_quote, author, language)

        session['start_time'] = time.time()
        return render_template('index.html', sentence=selected_quote, author=author, translation=translation, results=None, score=score, level=level, time_left=40)

# 제출 후 결과 계산 및 다음 단계로 이동
@app.route('/submit', methods=['POST'])
def submit():
    global score, level, mistake_counter, total_time_taken, total_cpm, total_errors, total_attempts
    start_time = session.get('start_time')
    if start_time is None:
        return redirect(url_for('index'))

    end_time = time.time()
    elapsed_time = end_time - start_time
    if elapsed_time > 40:
        elapsed_time = 40  # 시간 초과 시 40초로 고정
    time_left = max(0, 40 - elapsed_time)
    
    user_input = request.form.get('user_input', '')  # 입력된 내용 가져오기
    selected_sentence = request.form['sentence']

    results = calculate_results(user_input, selected_sentence, elapsed_time)  # 점수 계산

    # 통계 업데이트
    total_time_taken += elapsed_time
    score += results['score']

    # 선택한 언어 가져오기
    language = session.get('language', 'en')

    if len(level_sentences_used) == 0:
        if level < 10:
            level += 1
        else:
            # 레벨 10에서 모든 문장을 완료한 경우 게임 종료로 이동
            avg_cpm = total_cpm / total_attempts if total_attempts > 0 else 0
            most_common_mistake = mistake_counter.most_common(1)[0] if mistake_counter else ("없음", 0)
            return redirect(url_for('game_over', 
                                    total_time_taken=round(total_time_taken, 2),
                                    avg_cpm=round(avg_cpm, 2),
                                    total_errors=total_errors,
                                    most_common_mistake=most_common_mistake,
                                    total_score=int(score)))

    selected_quote, author, translation = get_next_quote(language)  # 언어 전달
    if selected_quote is None:  # 문장이 더 이상 없을 때 게임 종료
        avg_cpm = total_cpm / total_attempts if total_attempts > 0 else 0
        most_common_mistake = mistake_counter.most_common(1)[0] if mistake_counter else ("없음", 0)
        return redirect(url_for('game_over', 
                                total_time_taken=round(total_time_taken, 2),
                                avg_cpm=round(avg_cpm, 2),
                                total_errors=total_errors,
                                most_common_mistake=most_common_mistake,
                                total_score=int(score)))

    session['start_time'] = time.time()

    return render_template('index.html', sentence=selected_quote, author=author, translation=translation, results=results, score=int(score), level=level, time_left=time_left)

@app.route('/game_over')
def game_over():
    global score, total_time_taken, total_cpm, total_errors, total_attempts, mistake_counter

    avg_cpm = total_cpm / total_attempts if total_attempts > 0 else 0
    most_common_mistake = mistake_counter.most_common(1)[0] if mistake_counter else ("없음", 0)

    return render_template('game_over.html', 
                           total_time_taken=round(total_time_taken, 2),
                           avg_cpm=round(avg_cpm, 2),
                           total_errors=total_errors,
                           most_common_mistake=most_common_mistake,
                           total_score=int(score))


if __name__ == '__main__':
    app.run(debug=True)
