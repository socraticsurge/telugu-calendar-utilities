import { describe, expect, test } from 'vitest';

import {
  birthProfileCalculationActivation,
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
