import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../core/app_theme.dart';
import 'package:shared_preferences/shared_preferences.dart';

class PlanScreen extends StatefulWidget {
  const PlanScreen({Key? key}) : super(key: key);
  @override
  _PlanScreenState createState() => _PlanScreenState();
}

class _PlanScreenState extends State<PlanScreen> {
  List<dynamic> _actions = [];
  bool _loading = true;
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
    _fetchPlan();
  }

  Future<void> _fetchPlan() async {
    setState(() {
      _loading = true;
      _hasError = false;
    });
    try {
      final prefs = await SharedPreferences.getInstance();
      final uid = prefs.getString('user_id') ?? 'default';
      var res = await ApiClient.instance
          .get('/plan', queryParameters: {"user_id": uid});
      setState(() {
        _actions = res.data['actions'] ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _hasError = true;
        _loading = false;
      });
    }
  }

  Future<void> _markCompleted(String actionId) async {
    final prefs = await SharedPreferences.getInstance();
    final uid = prefs.getString('user_id') ?? 'default';
    await ApiClient.instance.post('/plan/action', data: {
      "user_id": uid,
      "action_id": actionId,
      "status": "completed",
    });
    _fetchPlan();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return _buildLoading();
    if (_hasError) return _buildError();
    if (_actions.isEmpty) return _buildEmpty();

    final pending = _actions.where((a) => a['status'] == 'pending').toList();
    final completed =
        _actions.where((a) => a['status'] != 'pending').toList();

    return RefreshIndicator(
      color: AppColors.primary,
      onRefresh: _fetchPlan,
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          // ── Summary header ────────────────────────────────────────────
          SliverToBoxAdapter(child: _buildSummaryHeader(pending.length)),

          // ── Pending section ───────────────────────────────────────────
          if (pending.isNotEmpty) ...[
            _buildSectionHeader('Pending Actions', pending.length,
                AppColors.statusPending),
            SliverList(
              delegate: SliverChildBuilderDelegate(
                (ctx, i) => _ActionCard(
                  action: pending[i],
                  onComplete: () => _markCompleted(pending[i]['action_id']),
                ),
                childCount: pending.length,
              ),
            ),
          ],

          // ── Completed section ─────────────────────────────────────────
          if (completed.isNotEmpty) ...[
            _buildSectionHeader(
                'Completed', completed.length, AppColors.statusDone),
            SliverList(
              delegate: SliverChildBuilderDelegate(
                (ctx, i) => _ActionCard(
                  action: completed[i],
                  onComplete: null,
                ),
                childCount: completed.length,
              ),
            ),
          ],

          // Bottom padding for floating nav
          const SliverToBoxAdapter(child: SizedBox(height: 100)),
        ],
      ),
    );
  }

  Widget _buildSummaryHeader(int pendingCount) {
    final total = _actions.length;
    final completedCount = total - pendingCount;
    final progress = total > 0 ? completedCount / total : 0.0;

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 12, 16, 4),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primary, AppColors.primaryLight],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: AppColors.cardShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Your Action Plan',
            style: TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w700,
              letterSpacing: -0.3,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '$completedCount of $total actions completed',
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 13,
              fontWeight: FontWeight.w400,
            ),
          ),
          const SizedBox(height: 16),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: progress,
              backgroundColor: Colors.white24,
              valueColor:
                  const AlwaysStoppedAnimation<Color>(Color(0xFF95E7A7)),
              minHeight: 8,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoading() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(
            color: AppColors.primary,
            strokeWidth: 2.5,
          ),
          SizedBox(height: 16),
          Text(
            'Loading your plan...',
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: AppColors.statusPendingBg,
              borderRadius: BorderRadius.circular(18),
            ),
            child: const Icon(
              Icons.wifi_off_rounded,
              color: AppColors.statusPending,
              size: 30,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Couldn\'t load plan',
            style: TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Check your connection and try again.',
            style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: _fetchPlan,
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: AppColors.accentSoft,
              borderRadius: BorderRadius.circular(24),
            ),
            child: const Icon(
              Icons.task_alt_rounded,
              color: AppColors.primary,
              size: 38,
            ),
          ),
          const SizedBox(height: 20),
          const Text(
            'No actions yet',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Chat with your coach to build\nyour personalised plan.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textSecondary, fontSize: 14, height: 1.5),
          ),
        ],
      ),
    );
  }

  SliverToBoxAdapter _buildSectionHeader(
      String title, int count, Color color) {
    return SliverToBoxAdapter(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 8),
        child: Row(
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
                letterSpacing: -0.2,
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                '$count',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: color,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Action Card ───────────────────────────────────────────────────────────────

class _ActionCard extends StatelessWidget {
  final dynamic action;
  final VoidCallback? onComplete;

  const _ActionCard({required this.action, this.onComplete});

  @override
  Widget build(BuildContext context) {
    final isPending = action['status'] == 'pending';
    final status = action['status'] as String? ?? '';

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        boxShadow: AppColors.cardShadow,
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Top row: target + status badge ────────────────────────
            Row(
              children: [
                Expanded(
                  child: Text(
                    action['target'] ?? '',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary,
                      letterSpacing: -0.2,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                _StatusBadge(status: status),
              ],
            ),
            const SizedBox(height: 10),

            // ── Divider ────────────────────────────────────────────────
            Container(
              height: 1,
              color: const Color(0xFFEAF2EC),
            ),
            const SizedBox(height: 10),

            // ── Action text ────────────────────────────────────────────
            Text(
              action['action_text'] ?? '',
              style: const TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
                height: 1.5,
              ),
            ),

            // ── Complete button ────────────────────────────────────────
            if (isPending && onComplete != null) ...[
              const SizedBox(height: 14),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: onComplete,
                  icon: const Icon(Icons.check_circle_outline_rounded, size: 18),
                  label: const Text('Mark as Completed'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 13),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String status;
  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    final isPending = status == 'pending';
    final bgColor = isPending
        ? AppColors.statusPendingBg
        : AppColors.statusDoneBg;
    final textColor = isPending
        ? const Color(0xFF9A6E00)
        : AppColors.statusDone;
    final icon = isPending ? Icons.schedule_rounded : Icons.check_circle_rounded;
    final label = isPending ? 'Pending' : 'Done';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: textColor),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: textColor,
              letterSpacing: 0.2,
            ),
          ),
        ],
      ),
    );
  }
}
