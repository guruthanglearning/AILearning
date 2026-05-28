import { Accordion } from "@/components/ui/Accordion";
import type { DecisionAids } from "@/types/api";

import { ChecklistSection } from "./ChecklistSection";
import { InstrumentPlaysSection } from "./InstrumentPlaysSection";
import { PositionSizingSection } from "./PositionSizingSection";
import { UserQuestionsSection } from "./UserQuestionsSection";
import { VolatilitySection } from "./VolatilitySection";

export function DecisionAidsPanel({ aids }: { aids: DecisionAids }) {
  return (
    <div className="space-y-2">
      <h2 className="text-sm font-medium text-gray-400">Decision Aids</h2>

      {aids.checklist.length > 0 && (
        <Accordion title="Checklist" defaultOpen={true}>
          <ChecklistSection items={aids.checklist} />
        </Accordion>
      )}

      {aids.volatility && (
        <Accordion title="Volatility Context">
          <VolatilitySection vol={aids.volatility} />
        </Accordion>
      )}

      {aids.instrument_plays.length > 0 && (
        <Accordion title="Instrument Plays">
          <InstrumentPlaysSection plays={aids.instrument_plays} />
        </Accordion>
      )}

      {aids.position_sizing.length > 0 && (
        <Accordion title="Position Sizing">
          <PositionSizingSection hints={aids.position_sizing} />
        </Accordion>
      )}

      {aids.user_questions.length > 0 && (
        <Accordion title="Reflective Questions">
          <UserQuestionsSection questions={aids.user_questions} answers={aids.user_answers ?? []} />
        </Accordion>
      )}
    </div>
  );
}
