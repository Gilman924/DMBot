from __future__ import annotations

import json
import logging

from discord.ext import commands

from ..runtime import SessionRuntime
from ..nat20_client import Nat20Error

log = logging.getLogger("dmbot.dnd")


class DnDCog(commands.Cog):
    def __init__(self, bot: commands.Bot, runtime: SessionRuntime) -> None:
        self.bot = bot
        self._rt = runtime

    async def cog_unload(self) -> None:
        await self._rt.nat20.close()

    @commands.command(name="dndstatus")
    async def dnd_status(self, ctx: commands.Context) -> None:
        """Prüft die Verbindung zur Nat20-D&D-Engine."""
        try:
            result = await self._rt.nat20.health()
            await ctx.send(
                "D&D-Engine erreichbar\n"
                f"Bridge: `{result.get('bridge', '?')}` | "
                f"Engine: `{result.get('engine', '?')}` | "
                f"Data: `{result.get('data', '?')}`"
            )
        except Nat20Error as exc:
            await ctx.send(f"Nat20-Verbindung fehlgeschlagen: `{exc}`")

    @commands.command(name="dndkampfstatus")
    async def dnd_combat_status(
        self, ctx: commands.Context, combat_id: str
    ) -> None:
        """Zeigt den aktuellen Zustand eines Nat20-Kampfes."""
        try:
            result = await self._rt.nat20.get_combat(combat_id)
            output = json.dumps(result, ensure_ascii=False, indent=2)
            if len(output) > 1800:
                output = output[:1800] + "\n... (gekürzt)"
            await ctx.send(f"```json\n{output}\n```")
        except Nat20Error as exc:
            await ctx.send(f"Kampfstatus konnte nicht geladen werden: `{exc}`")

    @commands.command(name="dndkampfende")
    async def dnd_combat_end(
        self, ctx: commands.Context, combat_id: str
    ) -> None:
        """Beendet einen Nat20-Kampf."""
        try:
            result = await self._rt.nat20.end_combat(combat_id)
            await ctx.send(f"Kampf `{combat_id}` beendet.")
            log.info("Nat20 combat %s ended: %s", combat_id, result)
        except Nat20Error as exc:
            await ctx.send(f"Kampf konnte nicht beendet werden: `{exc}`")
