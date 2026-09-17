import { deriveBirthProfile, searchBirthPlaces } from '../../lib/birth-profile-api';
import { GuestProfileStore, type GuestProfile, type GuestProfileSnapshot } from '../../lib/guest-profile-store';

export interface ProfilesPanelContext {
  returnTo?: string;
  onSaved?: (profile: GuestProfile) => void;
  focusTarget?: HTMLElement | null;
  requiredFor?: 'horoscope' | 'muhurta';
}

export interface ResolvedProfilesPanelContext extends ProfilesPanelContext {
  resolveFocusTarget?: () => HTMLElement | null;
}

export interface ProfilesPanelOptions {
  navigate: (tool: string) => void;
  onViewDailyHoroscope?: (profileId: string) => void;
  onFindMuhurtam?: (profileId: string) => void;
  root?: HTMLElement;
  searchPlaces?: typeof searchBirthPlaces;
  deriveProfile?: typeof deriveBirthProfile;
  birthCalculationEnabled?: boolean;
}

export interface ProfilesPanelController {
  openCreate(context?: ProfilesPanelContext): void;
  openView(profileId: string, context?: ProfilesPanelContext): void;
  openEdit(profileId: string, context?: ProfilesPanelContext): void;
  render(): void;
  destroy(): void;
}
export type PanelView =
  | { kind: 'list' }
  | { kind: 'detail'; profileId: string; context: ResolvedProfilesPanelContext }
  | { kind: 'create'; context: ResolvedProfilesPanelContext }
  | { kind: 'edit'; profileId: string; context: ResolvedProfilesPanelContext };

/** Internal dependencies; navigation state belongs only to the panel coordinator. */
export interface ProfilePanelHost {
  root: HTMLElement;
  store: GuestProfileStore;
  options: ProfilesPanelOptions;
  birthCalculationActive: boolean;
  controller: ProfilesPanelController;
  setView(view: PanelView): void;
  setFormMethod(method: 'birth-details' | 'manual'): void;
  renderIssue(snapshot: GuestProfileSnapshot): HTMLElement | null;
  renderList(): void;
  renderDetail(profileId: string, context: ResolvedProfilesPanelContext, focusHeading?: boolean): void;
  renderManualForm(mode: 'create' | 'edit', context: ResolvedProfilesPanelContext, profile?: GuestProfile): void;
  renderBirthForm(mode: 'create' | 'edit', context: ResolvedProfilesPanelContext, profile?: GuestProfile): void;
  returnToOrigin(context: ResolvedProfilesPanelContext, savedProfile?: GuestProfile): void;
}

export interface ProfileFormRequest {
  mode: 'create' | 'edit';
  context: ResolvedProfilesPanelContext;
  profile?: GuestProfile;
}
