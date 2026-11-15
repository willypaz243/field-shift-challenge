import { LocalStore } from "./store";
import { Outbox } from "./outbox";
import type { Transport } from "./types";

export class SyncClient {
  readonly outbox: Outbox;
  private pending: Promise<void> = Promise.resolve();

  constructor(
    readonly store: LocalStore,
    private transport: Transport,
  ) {
    this.outbox = new Outbox(store.db, transport);
  }

  refresh(zone: string, online: boolean) {
    if (!online) return Promise.resolve();
    const task = this.pending.then(() => this.sync(zone));
    this.pending = task.catch(() => undefined);
    return task;
  }

  private async sync(zone: string) {
    try {
      const state = await this.store.state(zone);
      const packet = await this.transport.pull(zone, state?.version);
      if (packet) await this.store.apply(zone, packet);
    } finally {
      await this.outbox.flush();
    }
  }
}
