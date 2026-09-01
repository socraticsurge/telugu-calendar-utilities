import { describe, expect, test } from 'vitest';

import {
  birthProfileCalculationActivation,
  electionChartCalculationActivation,
} from '../lib/remote-calculation-activation';

describe('birth-profile calculation activation', () => {
  test('defaults on for loopback development and off for public hosts', () => {
    expect(birthProfileCalculationActivation(
      { hostname: '127.0.0.1' } as Location,
      undefined,
    )).toEqual({ enabled: true, source: 'local-default' });
    expect(birthProfileCalculationActivation(
      { hostname: 'localhost' } as Location,
      undefined,
    )).toEqual({ enabled: true, source: 'local-default' });
    expect(birthProfileCalculationActivation(
      { hostname: '[::1]' } as Location,
      undefined,
    )).toEqual({ enabled: true, source: 'local-default' });
    expect(birthProfileCalculationActivation(
      { hostname: 'panchangam.astrochaganti.com' } as Location,
      undefined,
    )).toEqual({ enabled: false, source: 'disabled' });
  });

  test.each(['false', '', '1', 'yes', 'enabled', 'TRUE', ' true ', 'True'])(
    'fails closed for the explicit non-literal value %j',
    flag => {
      expect(birthProfileCalculationActivation(
        { hostname: '127.0.0.1' } as Location,
        flag,
      )).toEqual({ enabled: false, source: 'disabled' });
      expect(birthProfileCalculationActivation(
        { hostname: 'panchangam.astrochaganti.com' } as Location,
        flag,
      )).toEqual({ enabled: false, source: 'disabled' });
    },
  );

  test('accepts only the exact literal true value on a public host', () => {
    expect(birthProfileCalculationActivation(
      { hostname: 'panchangam.astrochaganti.com' } as Location,
      'true',
    )).toEqual({ enabled: true, source: 'explicit' });
  });
});

describe('election-chart calculation activation', () => {
  test('defaults on only for loopback development', () => {
    expect(electionChartCalculationActivation(
      { hostname: '127.0.0.1' } as Location,
      undefined,
    )).toEqual({ enabled: true, source: 'local-default' });
    expect(electionChartCalculationActivation(
      { hostname: 'localhost' } as Location,
      undefined,
    )).toEqual({ enabled: true, source: 'local-default' });
    expect(electionChartCalculationActivation(
      { hostname: '[::1]' } as Location,
      undefined,
    )).toEqual({ enabled: true, source: 'local-default' });
    expect(electionChartCalculationActivation(
      { hostname: 'panchangam.astrochaganti.com' } as Location,
      undefined,
    )).toEqual({ enabled: false, source: 'disabled' });
  });

  test.each(['false', '', '1', 'yes', 'enabled', 'TRUE', ' true ', 'True'])(
    'fails closed for the explicit non-literal value %j',
    flag => {
      expect(electionChartCalculationActivation(
        { hostname: '127.0.0.1' } as Location,
        flag,
      )).toEqual({ enabled: false, source: 'disabled' });
      expect(electionChartCalculationActivation(
        { hostname: 'panchangam.astrochaganti.com' } as Location,
        flag,
      )).toEqual({ enabled: false, source: 'disabled' });
    },
  );

  test('accepts only exact literal true on a public host', () => {
    expect(electionChartCalculationActivation(
      { hostname: 'panchangam.astrochaganti.com' } as Location,
      'true',
    )).toEqual({ enabled: true, source: 'explicit' });
  });

  test('is independent from the birth-profile activation flag', () => {
    const publicLocation = {
      hostname: 'panchangam.astrochaganti.com',
    } as Location;
    expect(birthProfileCalculationActivation(publicLocation, 'true').enabled).toBe(true);
    expect(electionChartCalculationActivation(publicLocation, undefined).enabled).toBe(false);
    expect(electionChartCalculationActivation(publicLocation, 'true').enabled).toBe(true);
    expect(birthProfileCalculationActivation(publicLocation, undefined).enabled).toBe(false);
  });
});
