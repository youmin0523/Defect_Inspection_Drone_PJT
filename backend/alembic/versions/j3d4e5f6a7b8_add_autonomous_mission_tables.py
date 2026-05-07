"""add autonomous mission tables

Revision ID: j3d4e5f6a7b8
Revises: i2c3d4e5f6a7
Create Date: 2026-05-07

자율비행(Indoor Autonomous Inspection) v1.1 도입을 위한 신규 테이블 4종.
- mission_plans      : 미션 메타·FSM 상태
- slam_pointclouds   : Visual-Inertial SLAM 키프레임 점군 메타
- coverage_grids     : 룸별 3D 그리드 셀(상하 포함) 캡처 상태
- room_topologies    : 룸 분리 그래프 (도어웨이 엣지 포함)

DB 기동은 최종 단계에서 일괄 적용 예정 — 본 마이그레이션은 코드 선(先) 완성용.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "j3d4e5f6a7b8"
down_revision: Union[str, None] = "i2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MISSION_STATUS_VALUES = ("pending", "running", "paused", "completed", "aborted", "failsafe")
MISSION_PHASE_VALUES = (
    "idle", "arm", "takeoff", "mapping", "verification", "path_plan",
    "coverage_fly", "room_transition", "complete", "land", "failsafe",
)


def upgrade() -> None:
    bind = op.get_bind()

    mission_status_enum = sa.Enum(*MISSION_STATUS_VALUES, name="mission_status_enum")
    mission_phase_enum = sa.Enum(*MISSION_PHASE_VALUES, name="mission_phase_enum")
    mission_status_enum.create(bind, checkfirst=True)
    mission_phase_enum.create(bind, checkfirst=True)

    # ── mission_plans ───────────────────────
    op.create_table(
        "mission_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("schedule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operator_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum(*MISSION_STATUS_VALUES, name="mission_status_enum", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "current_phase",
            sa.Enum(*MISSION_PHASE_VALUES, name="mission_phase_enum", create_type=False),
            nullable=False,
            server_default="idle",
        ),
        sa.Column("current_room_idx", sa.Integer(), nullable=True),
        sa.Column("params_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("plan_json", postgresql.JSONB(), nullable=True),
        sa.Column("failure_reason", sa.String(200), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["schedule_id"], ["inspection_schedules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["operator_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_mission_plans_site_id", "mission_plans", ["site_id"])
    op.create_index("idx_mission_site_status", "mission_plans", ["site_id", "status"])
    op.create_index(
        "idx_mission_status_created",
        "mission_plans",
        ["status", sa.text("created_at DESC")],
    )

    # ── slam_pointclouds ────────────────────
    op.create_table(
        "slam_pointclouds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("frame_idx", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("point_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pose_x", sa.Float(), nullable=True),
        sa.Column("pose_y", sa.Float(), nullable=True),
        sa.Column("pose_z", sa.Float(), nullable=True),
        sa.Column("pose_qw", sa.Float(), nullable=True),
        sa.Column("pose_qx", sa.Float(), nullable=True),
        sa.Column("pose_qy", sa.Float(), nullable=True),
        sa.Column("pose_qz", sa.Float(), nullable=True),
        sa.Column("slam_confidence", sa.Float(), nullable=True),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["mission_id"], ["mission_plans.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_slam_pointclouds_mission_id", "slam_pointclouds", ["mission_id"])
    op.create_index(
        "idx_pointcloud_mission_frame",
        "slam_pointclouds",
        ["mission_id", "frame_idx"],
        unique=True,
    )
    op.create_index(
        "idx_pointcloud_mission_ts",
        "slam_pointclouds",
        ["mission_id", sa.text("ts DESC")],
    )

    # ── coverage_grids ──────────────────────
    op.create_table(
        "coverage_grids",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_idx", sa.Integer(), nullable=False),
        sa.Column("cell_x", sa.Integer(), nullable=False),
        sa.Column("cell_y", sa.Integer(), nullable=False),
        sa.Column("cell_z", sa.Integer(), nullable=False),
        sa.Column("world_x", sa.Float(), nullable=False),
        sa.Column("world_y", sa.Float(), nullable=False),
        sa.Column("world_z", sa.Float(), nullable=False),
        sa.Column("captured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rgb_image_id", sa.String(128), nullable=True),
        sa.Column("thermal_image_id", sa.String(128), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("face_kind", sa.String(16), nullable=False, server_default="wall"),
        sa.Column("face_idx", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cam_pitch_rad", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["mission_id"], ["mission_plans.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "mission_id", "room_idx", "cell_x", "cell_y", "cell_z",
            name="uq_coverage_cell",
        ),
    )
    op.create_index("ix_coverage_grids_mission_id", "coverage_grids", ["mission_id"])
    op.create_index("ix_coverage_grids_captured", "coverage_grids", ["captured"])
    op.create_index(
        "idx_coverage_mission_room_cap",
        "coverage_grids",
        ["mission_id", "room_idx", "captured"],
    )

    # ── room_topologies ─────────────────────
    op.create_table(
        "room_topologies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nodes_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("edges_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["mission_id"], ["mission_plans.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_room_topology_mission", "room_topologies", ["mission_id"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_room_topology_mission", table_name="room_topologies")
    op.drop_table("room_topologies")

    op.drop_index("idx_coverage_mission_room_cap", table_name="coverage_grids")
    op.drop_index("ix_coverage_grids_captured", table_name="coverage_grids")
    op.drop_index("ix_coverage_grids_mission_id", table_name="coverage_grids")
    op.drop_table("coverage_grids")

    op.drop_index("idx_pointcloud_mission_ts", table_name="slam_pointclouds")
    op.drop_index("idx_pointcloud_mission_frame", table_name="slam_pointclouds")
    op.drop_index("ix_slam_pointclouds_mission_id", table_name="slam_pointclouds")
    op.drop_table("slam_pointclouds")

    op.drop_index("idx_mission_status_created", table_name="mission_plans")
    op.drop_index("idx_mission_site_status", table_name="mission_plans")
    op.drop_index("ix_mission_plans_site_id", table_name="mission_plans")
    op.drop_table("mission_plans")

    op.execute("DROP TYPE IF EXISTS mission_phase_enum")
    op.execute("DROP TYPE IF EXISTS mission_status_enum")
