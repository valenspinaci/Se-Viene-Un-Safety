
export type Year = number;
export type Event = string;
export type Session = string;
export type Driver = string;

export enum ExportType {
  LAPS = 'laps',
  TELEMETRY = 'telemetry',
  COMPARE = 'compare',
  TEAM_PARTNERS = 'team_partners',
  FINAL_SPEED = 'final_speed',
  RACE_PACE = 'race_pace',
  POLE_MICROSECTORS = 'pole_microsectors'
}

export enum LapSelector {
  FASTEST = 'fastest',
  LAP_NUMBER = 'lap_number'
}

export interface OptionsState {
  years: Year[];
  events: Event[];
  sessions: Session[];
  drivers: Driver[];
}

export interface SelectionState {
  year: string;
  event: string;
  session: string;
  selectedDrivers: Driver[];
  type: ExportType;
  lap: LapSelector;
  lapNumber: string;
}
