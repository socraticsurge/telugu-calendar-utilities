import { describe, expect, test } from 'vitest';

import activityArtifact from '../../data/activity-rules.generated.json';
import electionArtifact from '../../data/election-chart-rules.generated.json';
import { roleForActivity } from '../personal-election-screening';

type ManualCheckRow = {
  id: string;
  source_index: number;
  source_text: string;
  text: string;
  class: string;
  display_section: string;
  applicable_varas?: string[];
  purpose?: string;
};

type ActivityCheck = {
  deterministic_panchangam_fields: string[];
  personal_rule_ids: string[];
  election_chart_rule_ids: string[];
  manual_checks: ManualCheckRow[];
};

const rules = activityArtifact.rules as Record<string, Record<string, unknown>>;
const contract = activityArtifact.check_contract;
const activities = contract.activities as Record<string, ActivityCheck>;
const electionRules = electionArtifact.rules as Record<string, Array<{ id: string }>>;

describe('generated activity-check contract', () => {
  test('covers every browser activity and every canonical manual check', () => {
    expect(Object.keys(activities)).toEqual(Object.keys(rules));
    expect(contract.schema_version).toBe(2);
    expect(contract.manual_check_class).toBe('manual-only');
    expect(contract.display_sections).toEqual(['chart', 'information', 'practical']);
    expect(contract.purposes).toEqual(['safety_override']);

    const ids = new Set<string>();
    for (const [activity, rule] of Object.entries(rules)) {
      const entry = activities[activity];
      const sourceChecks = (rule.manual_checks || []) as string[];
      const coveredIndexes = new Set<number>();
      for (const row of entry.manual_checks) {
        expect(ids.has(row.id)).toBe(false);
        ids.add(row.id);
        expect(row.class).toBe('manual-only');
        expect(contract.display_sections).toContain(row.display_section);
        expect(row.text.trim()).not.toBe('');
        expect(row.source_text).toBe(sourceChecks[row.source_index]);
        coveredIndexes.add(row.source_index);
      }
      expect([...coveredIndexes].sort((a, b) => a - b)).toEqual(
        sourceChecks.map((_, index) => index),
      );
    }
  });

  test('lists only fields and exact-rule IDs available to each activity', () => {
    for (const [activity, entry] of Object.entries(activities)) {
      for (const field of entry.deterministic_panchangam_fields) {
        expect(Object.hasOwn(rules[activity], field)).toBe(true);
      }
      expect(entry.election_chart_rule_ids).toEqual(
        (electionRules[activity] || []).map(rule => rule.id),
      );
      expect(entry.personal_rule_ids).toEqual(
        roleForActivity(activity)?.ruleIds || [],
      );
    }
  });

  test('represents the mixed home-entry check without runtime text inference', () => {
    const rows = activities.gruhapravesha.manual_checks.filter(
      row => row.source_index === 3,
    );
    expect(rows.map(row => row.display_section)).toEqual(['chart', 'information']);
    expect(rows[0].text).not.toContain('Bhootabali');
    expect(rows[1].text).toContain('Bhootabali');

    expect(activities.gruhapravesha.manual_checks[2].display_section).toBe('chart');
    expect(activities.court.manual_checks[4].display_section).toBe('chart');
    expect(activities.purchase.manual_checks[2].display_section).toBe('information');
  });

  test('declares narrow weekday applicability without hiding source notes', () => {
    expect(activities.business_inventory_purchase.manual_checks[1].applicable_varas)
      .toEqual(['Shanivaram']);
    expect(activities.upanayana.manual_checks[1].applicable_varas)
      .toEqual(['Budhavaram']);
    expect(activities.home_repair.manual_checks[1].applicable_varas)
      .toEqual(['Somavaram', 'Shukravaram']);

    for (const [activity, index] of [
      ['purchase', 1],
      ['lending_money', 4],
      ['wedding', 5],
      ['gruhapravesha', 5],
    ] as const) {
      expect(activities[activity].manual_checks[index].applicable_varas)
        .toBeUndefined();
    }
  });

  test('marks safety overrides by purpose instead of text vocabulary', () => {
    const marked = Object.entries(activities).flatMap(([activity, entry]) =>
      entry.manual_checks
        .filter(row => row.purpose === 'safety_override')
        .map(row => [activity, row.source_index, row.display_section]),
    );
    expect(marked).toEqual([
      ['court', 5, 'practical'],
      ['surgery', 0, 'practical'],
    ]);
  });
});
