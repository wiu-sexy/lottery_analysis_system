import requests
import json
from datetime import datetime, date, timedelta
from src.models.lottery import db, LotteryResult, NumberFrequency, PredictionResult
from sqlalchemy import and_, or_, func
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LotteryService:
    
    API_BASE_URL = "https://gdwechat.daguoxiaoxian.com/api/lottery-results/list"
    
    @staticmethod
    def fetch_lottery_data(type_id=1, limit=30, page=1):
        """从API获取六合彩数据"""
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://gdwechat.daguoxiaoxian.com/frontend/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        params = {
            'type': type_id,
            'limit': limit,
            'page': page
        }
        
        try:
            response = requests.get(LotteryService.API_BASE_URL, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return None
    
    @staticmethod
    def save_lottery_results(data_list):
        """保存六合彩结果到数据库"""
        saved_count = 0
        updated_count = 0
        
        for item in data_list:
            try:
                # 检查是否已存在
                existing = LotteryResult.query.filter_by(original_id=item['id']).first()
                
                # 解析中奖号码
                red_balls, blue_ball = LotteryResult.parse_win_code(item['win_code'])
                if red_balls is None or blue_ball is None:
                    logger.warning(f"无法解析中奖号码: {item['win_code']}")
                    continue
                
                # 转换日期
                lottery_date = datetime.strptime(item['lottery_date'], '%Y-%m-%d').date()
                
                if existing:
                    # 更新现有记录
                    existing.type = item['type']
                    existing.type_name = item['type_name']
                    existing.issue_number = item['issue_number']
                    existing.lottery_date = lottery_date
                    existing.week = item['week']
                    existing.win_code = item['win_code']
                    existing.red_balls = red_balls
                    existing.blue_ball = blue_ball
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # 创建新记录
                    new_result = LotteryResult(
                        original_id=item['id'],
                        type=item['type'],
                        type_name=item['type_name'],
                        issue_number=item['issue_number'],
                        lottery_date=lottery_date,
                        week=item['week'],
                        win_code=item['win_code'],
                        red_balls=red_balls,
                        blue_ball=blue_ball
                    )
                    db.session.add(new_result)
                    saved_count += 1
                    
            except Exception as e:
                logger.error(f"保存数据失败: {item}, 错误: {e}")
                continue
        
        try:
            db.session.commit()
            logger.info(f"数据保存完成: 新增 {saved_count} 条, 更新 {updated_count} 条")
            return saved_count, updated_count
        except Exception as e:
            db.session.rollback()
            logger.error(f"数据库提交失败: {e}")
            return 0, 0
    
    @staticmethod
    def fetch_and_save_all_data(max_pages=100):
        """获取并保存所有可用数据"""
        total_saved = 0
        total_updated = 0
        page = 1
        
        while page <= max_pages:
            logger.info(f"正在获取第 {page} 页数据...")
            data = LotteryService.fetch_lottery_data(page=page, limit=100)
            
            if not data or data.get('code') != 1:
                logger.warning(f"第 {page} 页数据获取失败或无数据")
                break
                
            data_list = data.get('data', {}).get('list', [])
            if not data_list:
                logger.info(f"第 {page} 页无数据，停止获取")
                break
            
            saved, updated = LotteryService.save_lottery_results(data_list)
            total_saved += saved
            total_updated += updated
            
            page += 1
            
            # 如果这一页的数据量小于请求量，说明已经是最后一页
            if len(data_list) < 100:
                break
        
        logger.info(f"数据获取完成: 总共新增 {total_saved} 条, 更新 {total_updated} 条")
        return total_saved, total_updated
    
    @staticmethod
    def update_number_frequency():
        """更新号码频率统计"""
        logger.info("开始更新号码频率统计...")
        
        # 获取时间节点
        now = date.today()
        one_year_ago = now - timedelta(days=365)
        two_years_ago = now - timedelta(days=730)
        three_years_ago = now - timedelta(days=1095)
        
        # 清空现有频率数据
        NumberFrequency.query.delete()
        
        # 统计红球频率 (1-33)
        for number in range(1, 34):
            # 统计总频率
            total_freq = 0
            freq_1year = 0
            freq_2year = 0
            freq_3year = 0
            last_appeared = None
            
            # 查询包含该号码的所有记录
            results = LotteryResult.query.all()
            for result in results:
                red_balls = result.get_red_balls_list()
                if number in red_balls:
                    total_freq += 1
                    if result.lottery_date >= one_year_ago:
                        freq_1year += 1
                    if result.lottery_date >= two_years_ago:
                        freq_2year += 1
                    if result.lottery_date >= three_years_ago:
                        freq_3year += 1
                    
                    # 更新最后出现时间
                    if last_appeared is None or result.lottery_date > last_appeared:
                        last_appeared = result.lottery_date
            
            # 计算距离上次出现的天数
            days_since_last = (now - last_appeared).days if last_appeared else 9999
            
            # 保存红球频率
            freq_record = NumberFrequency(
                number=number,
                ball_type='red',
                frequency=total_freq,
                frequency_1year=freq_1year,
                frequency_2year=freq_2year,
                frequency_3year=freq_3year,
                last_appeared=last_appeared,
                days_since_last=days_since_last
            )
            db.session.add(freq_record)
        
        # 统计蓝球频率 (1-16)
        for number in range(1, 17):
            # 统计总频率
            total_freq = LotteryResult.query.filter_by(blue_ball=number).count()
            freq_1year = LotteryResult.query.filter(
                and_(LotteryResult.blue_ball == number, LotteryResult.lottery_date >= one_year_ago)
            ).count()
            freq_2year = LotteryResult.query.filter(
                and_(LotteryResult.blue_ball == number, LotteryResult.lottery_date >= two_years_ago)
            ).count()
            freq_3year = LotteryResult.query.filter(
                and_(LotteryResult.blue_ball == number, LotteryResult.lottery_date >= three_years_ago)
            ).count()
            
            # 获取最后出现时间
            last_result = LotteryResult.query.filter_by(blue_ball=number).order_by(
                LotteryResult.lottery_date.desc()
            ).first()
            last_appeared = last_result.lottery_date if last_result else None
            days_since_last = (now - last_appeared).days if last_appeared else 9999
            
            # 保存蓝球频率
            freq_record = NumberFrequency(
                number=number,
                ball_type='blue',
                frequency=total_freq,
                frequency_1year=freq_1year,
                frequency_2year=freq_2year,
                frequency_3year=freq_3year,
                last_appeared=last_appeared,
                days_since_last=days_since_last
            )
            db.session.add(freq_record)
        
        try:
            db.session.commit()
            logger.info("号码频率统计更新完成")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"号码频率统计更新失败: {e}")
            return False
    
    @staticmethod
    def get_trend_analysis(years=1):
        """获取趋势分析数据"""
        end_date = date.today()
        start_date = end_date - timedelta(days=365 * years)
        
        # 获取指定时间范围内的数据
        results = LotteryResult.query.filter(
            LotteryResult.lottery_date >= start_date
        ).order_by(LotteryResult.lottery_date.desc()).all()
        
        if not results:
            return None
        
        # 统计分析
        analysis = {
            'period': f'{years}年',
            'total_draws': len(results),
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'hot_red_numbers': [],
            'cold_red_numbers': [],
            'hot_blue_numbers': [],
            'cold_blue_numbers': [],
            'number_trends': [],
            'recent_patterns': []
        }
        
        # 统计红球出现频率
        red_counter = Counter()
        blue_counter = Counter()
        
        for result in results:
            red_balls = result.get_red_balls_list()
            for ball in red_balls:
                red_counter[ball] += 1
            blue_counter[result.blue_ball] += 1
        
        # 获取热号和冷号
        analysis['hot_red_numbers'] = red_counter.most_common(10)
        analysis['cold_red_numbers'] = red_counter.most_common()[:-11:-1]  # 最少的10个
        analysis['hot_blue_numbers'] = blue_counter.most_common(5)
        analysis['cold_blue_numbers'] = blue_counter.most_common()[:-6:-1]  # 最少的5个
        
        # 最近的开奖模式
        recent_results = results[:10]  # 最近10期
        analysis['recent_patterns'] = [
            {
                'issue': result.issue_number,
                'date': result.lottery_date.strftime('%Y-%m-%d'),
                'win_code': result.win_code,
                'red_balls': result.get_red_balls_list(),
                'blue_ball': result.blue_ball
            }
            for result in recent_results
        ]
        
        return analysis
    
    @staticmethod
    def get_latest_issue():
        """获取最新期号"""
        latest = LotteryResult.query.order_by(LotteryResult.lottery_date.desc()).first()
        return latest.issue_number if latest else None



    @staticmethod
    def get_consecutive_and_span_analysis(years=1):
        """获取连号和跨度分析数据"""
        end_date = date.today()
        start_date = end_date - timedelta(days=365 * years)
        
        results = LotteryResult.query.filter(
            LotteryResult.lottery_date >= start_date
        ).order_by(LotteryResult.lottery_date.desc()).all()
        
        if not results:
            return None
        
        consecutive_counts = Counter() # 连号次数
        span_counts = Counter()        # 跨度次数
        
        for result in results:
            red_balls = sorted(result.get_red_balls_list())
            
            # 连号分析
            current_consecutive = 0
            for i in range(len(red_balls) - 1):
                if red_balls[i+1] - red_balls[i] == 1:
                    current_consecutive += 1
                else:
                    if current_consecutive > 0:
                        consecutive_counts[current_consecutive + 1] += 1 # 连号长度
                    current_consecutive = 0
            if current_consecutive > 0:
                consecutive_counts[current_consecutive + 1] += 1
            
            # 跨度分析 (最大红球 - 最小红球)
            if len(red_balls) > 1:
                span = red_balls[-1] - red_balls[0]
                span_counts[span] += 1
                
        return {
            "period": f"{years}年",
            "total_draws": len(results),
            "consecutive_numbers_distribution": dict(consecutive_counts),
            "span_distribution": dict(span_counts)
        }


