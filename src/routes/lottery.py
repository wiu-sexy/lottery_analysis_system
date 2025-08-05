from flask import Blueprint, jsonify, request
from src.models.lottery import db, LotteryResult, NumberFrequency, PredictionResult
from src.services.lottery_service import LotteryService
from datetime import datetime, date, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

lottery_bp = Blueprint('lottery', __name__)

@lottery_bp.route('/fetch-data', methods=['POST'])
def fetch_lottery_data():
    """获取并保存六合彩数据"""
    try:
        # 获取请求参数
        data = request.get_json() or {}
        max_pages = data.get('max_pages', 10)  # 默认获取10页数据
        
        # 获取并保存数据
        saved, updated = LotteryService.fetch_and_save_all_data(max_pages=max_pages)
        
        # 更新频率统计
        LotteryService.update_number_frequency()
        
        return jsonify({
            'code': 1,
            'message': '数据获取成功',
            'data': {
                'saved_count': saved,
                'updated_count': updated,
                'total_records': LotteryResult.query.count()
            }
        })
        
    except Exception as e:
        logger.error(f"数据获取失败: {e}")
        return jsonify({
            'code': 0,
            'message': f'数据获取失败: {str(e)}',
            'data': None
        }), 500

@lottery_bp.route('/results', methods=['GET'])
def get_lottery_results():
    """获取六合彩开奖结果"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        years = request.args.get('years', type=int)  # 可选：按年份筛选
        
        # 构建查询
        query = LotteryResult.query
        
        if years:
            start_date = date.today() - timedelta(days=365 * years)
            query = query.filter(LotteryResult.lottery_date >= start_date)
        
        # 分页查询
        pagination = query.order_by(LotteryResult.lottery_date.desc()).paginate(
            page=page, per_page=limit, error_out=False
        )
        
        results = [result.to_dict() for result in pagination.items]
        
        return jsonify({
            'code': 1,
            'message': '查询成功',
            'data': {
                'list': results,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        })
        
    except Exception as e:
        logger.error(f"查询开奖结果失败: {e}")
        return jsonify({
            'code': 0,
            'message': f'查询失败: {str(e)}',
            'data': None
        }), 500

@lottery_bp.route('/trend-analysis', methods=['GET'])
def get_trend_analysis():
    """获取趋势分析数据"""
    try:
        years = request.args.get('years', 1, type=int)
        
        if years not in [1, 2, 3]:
            years = 1
        
        analysis = LotteryService.get_trend_analysis(years=years)
        
        if not analysis:
            return jsonify({
                'code': 0,
                'message': '暂无数据',
                'data': None
            })
        
        return jsonify({
            'code': 1,
            'message': '分析成功',
            'data': analysis
        })
        
    except Exception as e:
        logger.error(f"趋势分析失败: {e}")
        return jsonify({
            'code': 0,
            'message': f'分析失败: {str(e)}',
            'data': None
        }), 500

@lottery_bp.route('/number-frequency', methods=['GET'])
def get_number_frequency():
    """获取号码频率统计"""
    try:
        ball_type = request.args.get('type', 'all')  # 'red', 'blue', 'all'
        sort_by = request.args.get('sort', 'frequency')  # 'frequency', 'days_since_last'
        order = request.args.get('order', 'desc')  # 'asc', 'desc'
        
        query = NumberFrequency.query
        
        if ball_type in ['red', 'blue']:
            query = query.filter_by(ball_type=ball_type)
        
        # 排序
        if sort_by == 'frequency':
            if order == 'desc':
                query = query.order_by(NumberFrequency.frequency.desc())
            else:
                query = query.order_by(NumberFrequency.frequency.asc())
        elif sort_by == 'days_since_last':
            if order == 'desc':
                query = query.order_by(NumberFrequency.days_since_last.desc())
            else:
                query = query.order_by(NumberFrequency.days_since_last.asc())
        
        frequencies = query.all()
        result = [freq.to_dict() for freq in frequencies]
        
        return jsonify({
            'code': 1,
            'message': '查询成功',
            'data': {
                'frequencies': result,
                'summary': {
                    'red_count': len([f for f in result if f['ball_type'] == 'red']),
                    'blue_count': len([f for f in result if f['ball_type'] == 'blue']),
                    'total_count': len(result)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"号码频率查询失败: {e}")
        return jsonify({
            'code': 0,
            'message': f'查询失败: {str(e)}',
            'data': None
        }), 500

@lottery_bp.route('/predict', methods=['POST'])
def predict_next_draw():
    """预测下一期开奖号码"""
    try:
        data = request.get_json() or {}
        algorithm = data.get('algorithm', 'frequency')  # 'frequency', 'trend', 'combined'
        
        # 获取最新期号
        latest_issue = LotteryService.get_latest_issue()
        if not latest_issue:
            return jsonify({
                'code': 0,
                'message': '无历史数据，无法预测',
                'data': None
            })
        
        # 生成下一期期号（简单递增）
        next_issue = str(int(latest_issue) + 1)
        
        # 根据算法进行预测
        if algorithm == 'frequency':
            prediction = predict_by_frequency()
        elif algorithm == 'trend':
            prediction = predict_by_trend()
        else:  # combined
            prediction = predict_by_combined()
        
        if not prediction:
            return jsonify({
                'code': 0,
                'message': '预测失败',
                'data': None
            })
        
        # 保存预测结果
        prediction_record = PredictionResult(
            prediction_date=date.today(),
            predicted_issue=next_issue,
            predicted_red_balls=','.join(map(str, prediction['red_balls'])),
            predicted_blue_ball=prediction['blue_ball'],
            predicted_win_code=','.join(map(str, prediction['red_balls'])) + f",{prediction['blue_ball']}",
            algorithm_used=algorithm,
            confidence_score=prediction.get('confidence', 0.5)
        )
        
        db.session.add(prediction_record)
        db.session.commit()
        
        return jsonify({
            'code': 1,
            'message': '预测成功',
            'data': {
                'predicted_issue': next_issue,
                'prediction': prediction,
                'algorithm': algorithm,
                'prediction_date': date.today().strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        logger.error(f"预测失败: {e}")
        return jsonify({
            'code': 0,
            'message': f'预测失败: {str(e)}',
            'data': None
        }), 500

@lottery_bp.route('/predictions', methods=['GET'])
def get_predictions():
    """获取历史预测记录"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        pagination = PredictionResult.query.order_by(
            PredictionResult.prediction_date.desc()
        ).paginate(page=page, per_page=limit, error_out=False)
        
        predictions = [pred.to_dict() for pred in pagination.items]
        
        return jsonify({
            'code': 1,
            'message': '查询成功',
            'data': {
                'list': predictions,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        })
        
    except Exception as e:
        logger.error(f"查询预测记录失败: {e}")
        return jsonify({
            'code': 0,
            'message': f'查询失败: {str(e)}',
            'data': None
        }), 500

@lottery_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取统计信息"""
    try:
        total_results = LotteryResult.query.count()
        total_predictions = PredictionResult.query.count()
        
        # 获取最新和最旧的记录
        latest_result = LotteryResult.query.order_by(LotteryResult.lottery_date.desc()).first()
        oldest_result = LotteryResult.query.order_by(LotteryResult.lottery_date.asc()).first()
        
        # 计算数据覆盖的时间范围
        date_range = None
        if latest_result and oldest_result:
            days_diff = (latest_result.lottery_date - oldest_result.lottery_date).days
            date_range = {
                'start': oldest_result.lottery_date.strftime('%Y-%m-%d'),
                'end': latest_result.lottery_date.strftime('%Y-%m-%d'),
                'days': days_diff
            }
        
        return jsonify({
            'code': 1,
            'message': '统计成功',
            'data': {
                'total_results': total_results,
                'total_predictions': total_predictions,
                'date_range': date_range,
                'latest_issue': latest_result.issue_number if latest_result else None,
                'latest_date': latest_result.lottery_date.strftime('%Y-%m-%d') if latest_result else None
            }
        })
        
    except Exception as e:
        logger.error(f"统计查询失败: {e}")
        return jsonify({
            'code': 0,
            'message': f'统计失败: {str(e)}',
            'data': None
        }), 500


def predict_by_frequency():
    """基于频率的预测算法"""
    try:
        # 获取红球频率（选择出现次数较多但最近没出现的号码）
        red_frequencies = NumberFrequency.query.filter_by(ball_type='red').order_by(
            NumberFrequency.frequency.desc(), 
            NumberFrequency.days_since_last.desc()
        ).limit(15).all()
        
        # 从前15个热号中随机选择6个
        import random
        selected_red = random.sample([f.number for f in red_frequencies], 6)
        selected_red.sort()
        
        # 获取蓝球频率
        blue_frequencies = NumberFrequency.query.filter_by(ball_type='blue').order_by(
            NumberFrequency.frequency.desc(),
            NumberFrequency.days_since_last.desc()
        ).limit(5).all()
        
        # 从前5个热号中随机选择1个
        selected_blue = random.choice([f.number for f in blue_frequencies])
        
        return {
            'red_balls': selected_red,
            'blue_ball': selected_blue,
            'confidence': 0.6,
            'method': '基于历史频率分析'
        }
        
    except Exception as e:
        logger.error(f"频率预测失败: {e}")
        return None

def predict_by_trend():
    """基于趋势的预测算法"""
    try:
        # 获取最近20期的数据
        recent_results = LotteryResult.query.order_by(
            LotteryResult.lottery_date.desc()
        ).limit(20).all()
        
        if len(recent_results) < 10:
            return None
        
        # 分析最近的号码趋势
        from collections import Counter
        recent_red_counter = Counter()
        recent_blue_counter = Counter()
        
        for result in recent_results:
            red_balls = result.get_red_balls_list()
            for ball in red_balls:
                recent_red_counter[ball] += 1
            recent_blue_counter[result.blue_ball] += 1
        
        # 选择最近出现较少但历史频率较高的号码
        red_frequencies = NumberFrequency.query.filter_by(ball_type='red').all()
        red_scores = {}
        
        for freq in red_frequencies:
            recent_count = recent_red_counter.get(freq.number, 0)
            # 计算综合得分：历史频率高但最近出现少
            score = freq.frequency * 0.7 + (20 - recent_count) * 0.3
            red_scores[freq.number] = score
        
        # 选择得分最高的6个红球
        import random
        top_red = sorted(red_scores.items(), key=lambda x: x[1], reverse=True)[:12]
        selected_red = sorted(random.sample([x[0] for x in top_red], 6))
        
        # 蓝球选择
        blue_frequencies = NumberFrequency.query.filter_by(ball_type='blue').all()
        blue_scores = {}
        
        for freq in blue_frequencies:
            recent_count = recent_blue_counter.get(freq.number, 0)
            score = freq.frequency * 0.7 + (20 - recent_count) * 0.3
            blue_scores[freq.number] = score
        
        top_blue = sorted(blue_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        selected_blue = random.choice([x[0] for x in top_blue])
        
        return {
            'red_balls': selected_red,
            'blue_ball': selected_blue,
            'confidence': 0.7,
            'method': '基于趋势分析'
        }
        
    except Exception as e:
        logger.error(f"趋势预测失败: {e}")
        return None

def predict_by_combined():
    """组合预测算法"""
    try:
        freq_pred = predict_by_frequency()
        trend_pred = predict_by_trend()
        
        if not freq_pred or not trend_pred:
            return freq_pred or trend_pred
        
        # 合并两种预测结果
        import random
        
        # 红球：从两种预测中各选3个，然后随机组合
        combined_red = list(set(freq_pred['red_balls'][:3] + trend_pred['red_balls'][:3]))
        if len(combined_red) < 6:
            # 如果不够6个，从剩余的号码中补充
            all_red = set(freq_pred['red_balls'] + trend_pred['red_balls'])
            while len(combined_red) < 6 and len(all_red) > len(combined_red):
                remaining = list(all_red - set(combined_red))
                combined_red.append(random.choice(remaining))
        
        selected_red = sorted(combined_red[:6])
        
        # 蓝球：随机选择一种预测结果
        selected_blue = random.choice([freq_pred['blue_ball'], trend_pred['blue_ball']])
        
        return {
            'red_balls': selected_red,
            'blue_ball': selected_blue,
            'confidence': 0.8,
            'method': '组合预测算法'
        }
        
    except Exception as e:
        logger.error(f"组合预测失败: {e}")
        return None



@lottery_bp.route("/consecutive-span-analysis", methods=["GET"])
def get_consecutive_span_analysis():
    """获取连号和跨度分析数据"""
    try:
        years = request.args.get("years", 1, type=int)
        
        if years not in [1, 2, 3]:
            years = 1
        
        analysis = LotteryService.get_consecutive_and_span_analysis(years=years)
        
        if not analysis:
            return jsonify({
                "code": 0,
                "message": "暂无数据",
                "data": None
            })
        
        return jsonify({
            "code": 1,
            "message": "分析成功",
            "data": analysis
        })
        
    except Exception as e:
        logger.error(f"连号和跨度分析失败: {e}")
        return jsonify({
            "code": 0,
            "message": f"分析失败: {str(e)}",
            "data": None
        }), 500


