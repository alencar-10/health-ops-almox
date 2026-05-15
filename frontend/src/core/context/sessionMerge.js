/** Evita que /current sobrescreva nomes já resolvidos (Discovery ou pós-switch). */
export const isWeakLabel = (name) =>
  !name || name === 'N/A' || name === 'unknown' || name.startsWith('ID ');

export const mergeSessionLabels = (prev, next, { unitCatalog = [], sectorCatalog = [] } = {}) => {
  if (!next) return prev;
  const merged = { ...next };

  if (
    prev?.unit?.id &&
    merged.unit?.id &&
    String(prev.unit.id) !== String(merged.unit.id) &&
    !isWeakLabel(prev.unit?.name)
  ) {
    merged.unit = { ...merged.unit, id: prev.unit.id, name: prev.unit.name };
  }
  if (
    prev?.sector?.id &&
    merged.sector?.id &&
    String(prev.sector.id) !== String(merged.sector.id) &&
    !isWeakLabel(prev.sector?.name)
  ) {
    merged.sector = { ...merged.sector, id: prev.sector.id, name: prev.sector.name };
  }

  const unitId = merged.unit?.id ?? prev?.unit?.id;
  const sectorId = merged.sector?.id ?? prev?.sector?.id;

  if (isWeakLabel(merged.unit?.name)) {
    const fromPrev = !isWeakLabel(prev?.unit?.name) ? prev.unit.name : null;
    const fromCatalog = unitCatalog.find((u) => String(u.key) === String(unitId))?.name;
    merged.unit = {
      ...merged.unit,
      name: fromPrev || fromCatalog || prev?.unit?.name || merged.unit?.name,
    };
  }

  if (isWeakLabel(merged.sector?.name)) {
    const fromPrev = !isWeakLabel(prev?.sector?.name) ? prev.sector.name : null;
    const fromCatalog = sectorCatalog.find((s) => String(s.key) === String(sectorId))?.name;
    merged.sector = {
      ...merged.sector,
      name: fromPrev || fromCatalog || prev?.sector?.name || merged.sector?.name,
    };
  }

  return merged;
};
