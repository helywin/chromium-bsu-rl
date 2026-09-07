/*
 * Copyright (c) 2000 Mark B. Allan. All rights reserved.
 *
 * "Chromium B.S.U." is free software; you can redistribute
 * it and/or use it and/or modify it under the terms of the
 * "Clarified Artistic License"
 */
#ifndef MainGL_h
#define MainGL_h

class Global;

//====================================================================
class MainGL
{
public:
	MainGL();
	~MainGL();

	int		initGL();
	void	drawGL();
	void	drawGameGL();
	// RL local change 2026-09-07: explicit gameplay update boundary.
	void	updateGameLogic();
	void	advanceSimulationTick();
	void	renderGameFrame();
	void	drawDeadGL();
	void	drawSuccessGL();
	void	drawTextGL(const char *string, float pulse, float scale);
	void	reshapeGL( int w, int h );

	const char* findFont();
	void	loadTextures();
	void	deleteTextures();

private:
	Global	*game;
};

#endif // mainGL_h
