"""CAT session orchestrator — ties together all components."""
from dataclasses import dataclass, field

from ..models.irt_2pl import ItemParameters
from ..models.ability_estimator import estimate_theta_eap, estimate_initial_theta
from .item_selector import select_next_item, ContentTracker, ExposureController
from .stopping_rules import StoppingRules
from ..reporting.score_mapper import generate_diagnostic_report


@dataclass
class ResponseRecord:
    """Record of a single response during a test session."""
    item: ItemParameters
    response: int  # 1 = correct, 0 = incorrect
    theta_before: float
    theta_after: float
    se_before: float
    se_after: float
    sequence: int


@dataclass
class CATSession:
    """A complete CAT test session."""
    item_pool: list[ItemParameters]
    initial_theta: float = 0.0
    stopping_rules: StoppingRules = field(default_factory=StoppingRules)
    exposure_controller: ExposureController | None = None

    # Session state
    current_theta: float = 0.0
    current_se: float = 1.5
    administered_items: list[ItemParameters] = field(default_factory=list)
    responses: list[int] = field(default_factory=list)
    dont_know_flags: list[bool] = field(default_factory=list)
    theta_history: list[float] = field(default_factory=list)
    response_records: list[ResponseRecord] = field(default_factory=list)
    content_tracker: ContentTracker = field(default_factory=ContentTracker)
    is_complete: bool = False
    termination_reason: str = ""

    def __post_init__(self):
        self.current_theta = self.initial_theta
        self.theta_history = [self.initial_theta]

    @classmethod
    def create(
        cls,
        item_pool: list[ItemParameters],
        grade: str = "중2",
        self_assess: str = "intermediate",
        exam_experience: str = "none",
        knows_calibrator: bool | None = None,
        exposure_controller: ExposureController | None = None,
    ) -> "CATSession":
        """Create a new CAT session from user profile."""
        initial_theta = estimate_initial_theta(
            grade=grade,
            self_assess=self_assess,
            exam_experience=exam_experience,
            knows_calibrator=knows_calibrator,
        )
        return cls(
            item_pool=item_pool,
            initial_theta=initial_theta,
            exposure_controller=exposure_controller,
        )

    def get_next_item(self) -> ItemParameters | None:
        """Get the next item to administer."""
        if self.is_complete:
            return None

        administered_ids = {item.item_id for item in self.administered_items}
        return select_next_item(
            theta=self.current_theta,
            item_pool=self.item_pool,
            administered_ids=administered_ids,
            content_tracker=self.content_tracker,
            exposure_controller=self.exposure_controller,
        )

    def record_response(self, item: ItemParameters, is_correct: bool, is_dont_know: bool = False):
        """Record a response and update ability estimate.

        Args:
            item: The item that was answered
            is_correct: Whether the answer was correct
            is_dont_know: Whether the test-taker selected "Don't Know".
                In 3PL mode, this overrides guessing_c to 0 for this response,
                providing a cleaner signal than a random guess.
        """
        response = 1 if is_correct else 0
        theta_before = self.current_theta
        se_before = self.current_se

        # Update administered items and responses
        self.administered_items.append(item)
        self.responses.append(response)
        self.dont_know_flags.append(is_dont_know)
        self.content_tracker.record(item)

        # Re-estimate theta
        self.current_theta, self.current_se = estimate_theta_eap(
            items=self.administered_items,
            responses=self.responses,
            dont_know_flags=self.dont_know_flags,
        )
        self.theta_history.append(self.current_theta)

        # Record
        self.response_records.append(ResponseRecord(
            item=item,
            response=response,
            theta_before=theta_before,
            theta_after=self.current_theta,
            se_before=se_before,
            se_after=self.current_se,
            sequence=len(self.responses),
        ))

        # Check stopping criteria
        should_stop, reason = self.stopping_rules.should_stop(
            items_completed=len(self.responses),
            current_se=self.current_se,
            theta_history=self.theta_history,
        )
        if should_stop:
            self.is_complete = True
            self.termination_reason = reason
            if self.exposure_controller:
                self.exposure_controller.end_test()

    def get_results(self) -> dict:
        """Generate the final diagnostic report."""
        return generate_diagnostic_report(
            theta=self.current_theta,
            se=self.current_se,
            items_administered=self.administered_items,
            responses=self.responses,
            full_item_bank=self.item_pool,
        )

    def get_progress(self) -> dict:
        """Get current test progress."""
        total_correct = sum(self.responses)
        total = len(self.responses)
        return {
            "items_completed": total,
            "total_correct": total_correct,
            "accuracy": round(total_correct / total, 3) if total > 0 else 0,
            "current_theta": round(self.current_theta, 3),
            "current_se": round(self.current_se, 3),
            "is_complete": self.is_complete,
            "estimated_remaining": max(0, self.stopping_rules.min_items - total)
                if total < self.stopping_rules.min_items
                else "depends on SE convergence",
        }
