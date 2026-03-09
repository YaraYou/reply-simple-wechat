import { useSaveSettingsMutation, useSettingsQuery } from "../api/hooks";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { SettingsForm } from "../components/settings/SettingsForm";

export function SettingsPage() {
  const settingsQuery = useSettingsQuery();
  const saveMutation = useSaveSettingsMutation();

  if (settingsQuery.isLoading) return <LoadingState />;
  if (settingsQuery.isError) return <ErrorState message={settingsQuery.error.message} />;
  if (!settingsQuery.data) return <ErrorState message="No settings data" />;

  return (
    <section className="page-grid">
      <SettingsForm
        data={settingsQuery.data}
        saving={saveMutation.isPending}
        onSubmit={(payload) => saveMutation.mutate(payload)}
      />
    </section>
  );
}
