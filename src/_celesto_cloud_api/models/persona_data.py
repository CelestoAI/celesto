from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.persona_data_communication_preferences_type_0 import (
        PersonaDataCommunicationPreferencesType0,
    )
    from ..models.persona_data_company_context_type_0 import (
        PersonaDataCompanyContextType0,
    )
    from ..models.persona_data_motivators_type_0_item import (
        PersonaDataMotivatorsType0Item,
    )
    from ..models.persona_data_outreach_strategy_type_0 import (
        PersonaDataOutreachStrategyType0,
    )
    from ..models.persona_data_pain_points_type_0_item import (
        PersonaDataPainPointsType0Item,
    )
    from ..models.persona_data_professional_summary_type_0 import (
        PersonaDataProfessionalSummaryType0,
    )
    from ..models.persona_data_qualifying_questions_type_0_item import (
        PersonaDataQualifyingQuestionsType0Item,
    )


T = TypeVar("T", bound="PersonaData")


@_attrs_define
class PersonaData:
    """Schema for persona data used in outbound generation.

    Example:
        {'company': 'Nimbus Data', 'company_context': {'company_size': '50-200 employees', 'industry_focus': 'Data
            Analytics'}, 'name': 'Jordan Lee', 'problems': ['spread across tools', 'slow handoffs'], 'recent_post': 'revops
            tooling debt', 'role': 'VP Sales'}

    Attributes:
        name (None | str | Unset): Contact name
        role (None | str | Unset): Contact's job title/role
        company (None | str | Unset): Company name
        recent_post (None | str | Unset): Recent social media post or activity
        problems (list[str] | None | Unset): Identified pain points
        motivators (list[PersonaDataMotivatorsType0Item] | None | Unset):
        pain_points (list[PersonaDataPainPointsType0Item] | None | Unset):
        data_sources (list[str] | None | Unset):
        last_updated (datetime.datetime | None | Unset):
        company_context (None | PersonaDataCompanyContextType0 | Unset):
        confidence_score (float | None | Unset):
        outreach_strategy (None | PersonaDataOutreachStrategyType0 | Unset):
        professional_summary (None | PersonaDataProfessionalSummaryType0 | Unset):
        qualifying_questions (list[PersonaDataQualifyingQuestionsType0Item] | None | Unset):
        communication_preferences (None | PersonaDataCommunicationPreferencesType0 | Unset):
    """

    name: None | str | Unset = UNSET
    role: None | str | Unset = UNSET
    company: None | str | Unset = UNSET
    recent_post: None | str | Unset = UNSET
    problems: list[str] | None | Unset = UNSET
    motivators: list[PersonaDataMotivatorsType0Item] | None | Unset = UNSET
    pain_points: list[PersonaDataPainPointsType0Item] | None | Unset = UNSET
    data_sources: list[str] | None | Unset = UNSET
    last_updated: datetime.datetime | None | Unset = UNSET
    company_context: None | PersonaDataCompanyContextType0 | Unset = UNSET
    confidence_score: float | None | Unset = UNSET
    outreach_strategy: None | PersonaDataOutreachStrategyType0 | Unset = UNSET
    professional_summary: None | PersonaDataProfessionalSummaryType0 | Unset = UNSET
    qualifying_questions: (
        list[PersonaDataQualifyingQuestionsType0Item] | None | Unset
    ) = UNSET
    communication_preferences: (
        None | PersonaDataCommunicationPreferencesType0 | Unset
    ) = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.persona_data_communication_preferences_type_0 import (
            PersonaDataCommunicationPreferencesType0,
        )  # noqa: PLC0415
        from ..models.persona_data_company_context_type_0 import (
            PersonaDataCompanyContextType0,
        )  # noqa: PLC0415
        from ..models.persona_data_motivators_type_0_item import (
            PersonaDataMotivatorsType0Item,
        )  # noqa: PLC0415
        from ..models.persona_data_outreach_strategy_type_0 import (
            PersonaDataOutreachStrategyType0,
        )  # noqa: PLC0415
        from ..models.persona_data_pain_points_type_0_item import (
            PersonaDataPainPointsType0Item,
        )  # noqa: PLC0415
        from ..models.persona_data_professional_summary_type_0 import (
            PersonaDataProfessionalSummaryType0,
        )  # noqa: PLC0415
        from ..models.persona_data_qualifying_questions_type_0_item import (
            PersonaDataQualifyingQuestionsType0Item,
        )  # noqa: PLC0415

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        role: None | str | Unset
        if isinstance(self.role, Unset):
            role = UNSET
        else:
            role = self.role

        company: None | str | Unset
        if isinstance(self.company, Unset):
            company = UNSET
        else:
            company = self.company

        recent_post: None | str | Unset
        if isinstance(self.recent_post, Unset):
            recent_post = UNSET
        else:
            recent_post = self.recent_post

        problems: list[str] | None | Unset
        if isinstance(self.problems, Unset):
            problems = UNSET
        elif isinstance(self.problems, list):
            problems = self.problems

        else:
            problems = self.problems

        motivators: list[dict[str, Any]] | None | Unset
        if isinstance(self.motivators, Unset):
            motivators = UNSET
        elif isinstance(self.motivators, list):
            motivators = []
            for motivators_type_0_item_data in self.motivators:
                motivators_type_0_item = motivators_type_0_item_data.to_dict()
                motivators.append(motivators_type_0_item)

        else:
            motivators = self.motivators

        pain_points: list[dict[str, Any]] | None | Unset
        if isinstance(self.pain_points, Unset):
            pain_points = UNSET
        elif isinstance(self.pain_points, list):
            pain_points = []
            for pain_points_type_0_item_data in self.pain_points:
                pain_points_type_0_item = pain_points_type_0_item_data.to_dict()
                pain_points.append(pain_points_type_0_item)

        else:
            pain_points = self.pain_points

        data_sources: list[str] | None | Unset
        if isinstance(self.data_sources, Unset):
            data_sources = UNSET
        elif isinstance(self.data_sources, list):
            data_sources = self.data_sources

        else:
            data_sources = self.data_sources

        last_updated: None | str | Unset
        if isinstance(self.last_updated, Unset):
            last_updated = UNSET
        elif isinstance(self.last_updated, datetime.datetime):
            last_updated = self.last_updated.isoformat()
        else:
            last_updated = self.last_updated

        company_context: dict[str, Any] | None | Unset
        if isinstance(self.company_context, Unset):
            company_context = UNSET
        elif isinstance(self.company_context, PersonaDataCompanyContextType0):
            company_context = self.company_context.to_dict()
        else:
            company_context = self.company_context

        confidence_score: float | None | Unset
        if isinstance(self.confidence_score, Unset):
            confidence_score = UNSET
        else:
            confidence_score = self.confidence_score

        outreach_strategy: dict[str, Any] | None | Unset
        if isinstance(self.outreach_strategy, Unset):
            outreach_strategy = UNSET
        elif isinstance(self.outreach_strategy, PersonaDataOutreachStrategyType0):
            outreach_strategy = self.outreach_strategy.to_dict()
        else:
            outreach_strategy = self.outreach_strategy

        professional_summary: dict[str, Any] | None | Unset
        if isinstance(self.professional_summary, Unset):
            professional_summary = UNSET
        elif isinstance(self.professional_summary, PersonaDataProfessionalSummaryType0):
            professional_summary = self.professional_summary.to_dict()
        else:
            professional_summary = self.professional_summary

        qualifying_questions: list[dict[str, Any]] | None | Unset
        if isinstance(self.qualifying_questions, Unset):
            qualifying_questions = UNSET
        elif isinstance(self.qualifying_questions, list):
            qualifying_questions = []
            for qualifying_questions_type_0_item_data in self.qualifying_questions:
                qualifying_questions_type_0_item = (
                    qualifying_questions_type_0_item_data.to_dict()
                )
                qualifying_questions.append(qualifying_questions_type_0_item)

        else:
            qualifying_questions = self.qualifying_questions

        communication_preferences: dict[str, Any] | None | Unset
        if isinstance(self.communication_preferences, Unset):
            communication_preferences = UNSET
        elif isinstance(
            self.communication_preferences, PersonaDataCommunicationPreferencesType0
        ):
            communication_preferences = self.communication_preferences.to_dict()
        else:
            communication_preferences = self.communication_preferences

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if role is not UNSET:
            field_dict["role"] = role
        if company is not UNSET:
            field_dict["company"] = company
        if recent_post is not UNSET:
            field_dict["recent_post"] = recent_post
        if problems is not UNSET:
            field_dict["problems"] = problems
        if motivators is not UNSET:
            field_dict["motivators"] = motivators
        if pain_points is not UNSET:
            field_dict["pain_points"] = pain_points
        if data_sources is not UNSET:
            field_dict["data_sources"] = data_sources
        if last_updated is not UNSET:
            field_dict["last_updated"] = last_updated
        if company_context is not UNSET:
            field_dict["company_context"] = company_context
        if confidence_score is not UNSET:
            field_dict["confidence_score"] = confidence_score
        if outreach_strategy is not UNSET:
            field_dict["outreach_strategy"] = outreach_strategy
        if professional_summary is not UNSET:
            field_dict["professional_summary"] = professional_summary
        if qualifying_questions is not UNSET:
            field_dict["qualifying_questions"] = qualifying_questions
        if communication_preferences is not UNSET:
            field_dict["communication_preferences"] = communication_preferences

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.persona_data_communication_preferences_type_0 import (
            PersonaDataCommunicationPreferencesType0,
        )  # noqa: PLC0415
        from ..models.persona_data_company_context_type_0 import (
            PersonaDataCompanyContextType0,
        )  # noqa: PLC0415
        from ..models.persona_data_motivators_type_0_item import (
            PersonaDataMotivatorsType0Item,
        )  # noqa: PLC0415
        from ..models.persona_data_outreach_strategy_type_0 import (
            PersonaDataOutreachStrategyType0,
        )  # noqa: PLC0415
        from ..models.persona_data_pain_points_type_0_item import (
            PersonaDataPainPointsType0Item,
        )  # noqa: PLC0415
        from ..models.persona_data_professional_summary_type_0 import (
            PersonaDataProfessionalSummaryType0,
        )  # noqa: PLC0415
        from ..models.persona_data_qualifying_questions_type_0_item import (
            PersonaDataQualifyingQuestionsType0Item,
        )  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_role(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        role = _parse_role(d.pop("role", UNSET))

        def _parse_company(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        company = _parse_company(d.pop("company", UNSET))

        def _parse_recent_post(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        recent_post = _parse_recent_post(d.pop("recent_post", UNSET))

        def _parse_problems(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                problems_type_0 = cast(list[str], data)

                return problems_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        problems = _parse_problems(d.pop("problems", UNSET))

        def _parse_motivators(
            data: object,
        ) -> list[PersonaDataMotivatorsType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                motivators_type_0 = []
                _motivators_type_0 = data
                for motivators_type_0_item_data in _motivators_type_0:
                    motivators_type_0_item = PersonaDataMotivatorsType0Item.from_dict(
                        motivators_type_0_item_data
                    )

                    motivators_type_0.append(motivators_type_0_item)

                return motivators_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[PersonaDataMotivatorsType0Item] | None | Unset, data)

        motivators = _parse_motivators(d.pop("motivators", UNSET))

        def _parse_pain_points(
            data: object,
        ) -> list[PersonaDataPainPointsType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                pain_points_type_0 = []
                _pain_points_type_0 = data
                for pain_points_type_0_item_data in _pain_points_type_0:
                    pain_points_type_0_item = PersonaDataPainPointsType0Item.from_dict(
                        pain_points_type_0_item_data
                    )

                    pain_points_type_0.append(pain_points_type_0_item)

                return pain_points_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[PersonaDataPainPointsType0Item] | None | Unset, data)

        pain_points = _parse_pain_points(d.pop("pain_points", UNSET))

        def _parse_data_sources(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                data_sources_type_0 = cast(list[str], data)

                return data_sources_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        data_sources = _parse_data_sources(d.pop("data_sources", UNSET))

        def _parse_last_updated(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_updated_type_0 = datetime.datetime.fromisoformat(data)

                return last_updated_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_updated = _parse_last_updated(d.pop("last_updated", UNSET))

        def _parse_company_context(
            data: object,
        ) -> None | PersonaDataCompanyContextType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                company_context_type_0 = PersonaDataCompanyContextType0.from_dict(data)

                return company_context_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PersonaDataCompanyContextType0 | Unset, data)

        company_context = _parse_company_context(d.pop("company_context", UNSET))

        def _parse_confidence_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        confidence_score = _parse_confidence_score(d.pop("confidence_score", UNSET))

        def _parse_outreach_strategy(
            data: object,
        ) -> None | PersonaDataOutreachStrategyType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                outreach_strategy_type_0 = PersonaDataOutreachStrategyType0.from_dict(
                    data
                )

                return outreach_strategy_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PersonaDataOutreachStrategyType0 | Unset, data)

        outreach_strategy = _parse_outreach_strategy(d.pop("outreach_strategy", UNSET))

        def _parse_professional_summary(
            data: object,
        ) -> None | PersonaDataProfessionalSummaryType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                professional_summary_type_0 = (
                    PersonaDataProfessionalSummaryType0.from_dict(data)
                )

                return professional_summary_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PersonaDataProfessionalSummaryType0 | Unset, data)

        professional_summary = _parse_professional_summary(
            d.pop("professional_summary", UNSET)
        )

        def _parse_qualifying_questions(
            data: object,
        ) -> list[PersonaDataQualifyingQuestionsType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                qualifying_questions_type_0 = []
                _qualifying_questions_type_0 = data
                for (
                    qualifying_questions_type_0_item_data
                ) in _qualifying_questions_type_0:
                    qualifying_questions_type_0_item = (
                        PersonaDataQualifyingQuestionsType0Item.from_dict(
                            qualifying_questions_type_0_item_data
                        )
                    )

                    qualifying_questions_type_0.append(qualifying_questions_type_0_item)

                return qualifying_questions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[PersonaDataQualifyingQuestionsType0Item] | None | Unset, data
            )

        qualifying_questions = _parse_qualifying_questions(
            d.pop("qualifying_questions", UNSET)
        )

        def _parse_communication_preferences(
            data: object,
        ) -> None | PersonaDataCommunicationPreferencesType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                communication_preferences_type_0 = (
                    PersonaDataCommunicationPreferencesType0.from_dict(data)
                )

                return communication_preferences_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PersonaDataCommunicationPreferencesType0 | Unset, data)

        communication_preferences = _parse_communication_preferences(
            d.pop("communication_preferences", UNSET)
        )

        persona_data = cls(
            name=name,
            role=role,
            company=company,
            recent_post=recent_post,
            problems=problems,
            motivators=motivators,
            pain_points=pain_points,
            data_sources=data_sources,
            last_updated=last_updated,
            company_context=company_context,
            confidence_score=confidence_score,
            outreach_strategy=outreach_strategy,
            professional_summary=professional_summary,
            qualifying_questions=qualifying_questions,
            communication_preferences=communication_preferences,
        )

        persona_data.additional_properties = d
        return persona_data

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
